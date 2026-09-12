import io
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import pytest
from PIL import Image
from sqlalchemy import func, select

from app.api.dependencies import token_hash
from app.core.config import Settings, settings
from app.models import AuthSession, Diagnosis, Document, Medication, Operation
from app.services import document_parser
from app.services.document_parser import ParserError, prepare_images, validate_extraction
from tests.conftest import TestingSessionLocal


def signup(client, email="patient@example.com"):
    response = client.post("/auth/signup", json={"email": email, "password": "secret123"})
    assert response.status_code == 201
    return response.json()


def headers(user):
    return {"Authorization": f"Bearer {user['token']}"}


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(output, format="PNG")
    return output.getvalue()


def extraction(context):
    ids = {name: str(uuid4()) for name in ("org", "doctor", "medication", "operation", "diagnosis", "visit", "recommendation")}
    common = {
        "patient_id": context["patient_id"], "doctor_id": ids["doctor"], "med_org_id": ids["org"],
        "document_id": context["document_id"], "created_at": context["ingested_at"][:10],
    }
    return {
        "schema_version": "3.0", "document_type": "medical_history_db_import",
        "patient": {"id": context["patient_id"], "created_at": context["ingested_at"][:10]},
        "documents": [{"id": context["document_id"], "s3_url": context["s3_url"],
                       "created_at": context["ingested_at"], "type": "discharge_summary"}],
        "medical_organizations": [{"id": ids["org"], "name": "Test clinic"}],
        "doctors": [{"id": ids["doctor"], "full_name": "Test doctor", "med_org_id": ids["org"]}],
        "medications": [{**common, "id": ids["medication"], "name": "Recorded drug", "dosage": 5}],
        "operations": [{**common, "id": ids["operation"], "name": "Recorded surgery", "type": "surgery",
                        "performed_at": "2020", "document_id": None}],
        "diagnoses": [{**common, "id": ids["diagnosis"], "name": "Recorded diagnosis", "icd_10_code": None,
                       "diagnosis_type": "primary", "status": "confirmed"}],
        "recommendations": [{**common, "id": ids["recommendation"], "category": "follow_up", "text": "Recorded follow-up"}],
        "medical_visits": [{**common, "id": ids["visit"], "created_at": context["ingested_at"],
                            "visit_type": "hospitalization", "complaints": [],
                            "anamnesis": {key: "" for key in ("present_illness", "past_medical_history", "epidemiological_history",
                                                               "family_history", "social_history", "reproductive_history")},
                            "examination": {"general_status": "", "vital_signs": [], "findings": []},
                            "diagnosis_ids": [ids["diagnosis"]], "recommendation_ids": [ids["recommendation"]]}],
    }


@pytest.fixture
def grok(monkeypatch):
    monkeypatch.setattr(settings, "xai_api_key", "test-key")
    requests = []
    original_client = httpx.Client

    def handler(request):
        assert request.url == "https://api.x.ai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        requests.append(payload)
        text = payload["messages"][1]["content"][0]["text"]
        context = json.loads(text.split("DOCUMENT_CONTEXT:\n")[1].split("\nSOURCE_IMAGES:")[0])
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {
            "content": json.dumps(extraction(context)),
        }}]})

    monkeypatch.setattr(document_parser.httpx, "Client", lambda **kwargs: original_client(
        transport=httpx.MockTransport(handler), **kwargs,
    ))
    return requests


def test_frontend_auth_profile_logout(client):
    user = signup(client)
    auth = headers(user)
    assert user["profileComplete"] is False
    assert client.get("/me", headers=auth).json()["id"] == user["id"]
    assert client.get("/me/profile", headers=auth).json()["heightCm"] == ""
    profile = {"heightCm": "180", "weightKg": "75", "age": "30", "sex": "male", "comments": ""}
    assert client.put("/me/profile", headers=auth, json=profile).json()["profileComplete"] is True
    assert client.get("/me/profile", headers=auth).json() == profile
    assert client.put("/me/profile", headers=auth, json={**profile, "heightCm": "NaN"}).status_code == 422
    assert client.post("/auth/logout", headers=auth).status_code == 204
    assert client.get("/me", headers=auth).status_code == 401
    response = client.post("/auth/login", json={"email": "PATIENT@example.com", "password": "secret123"})
    assert response.status_code == 200
    assert response.json()["profileComplete"] is True
    assert client.post("/auth/login", json={"email": user["email"], "password": "incorrect"}).status_code == 401


def test_session_expiry_and_password_limit(client):
    user = signup(client)
    with TestingSessionLocal() as db:
        session = db.get(AuthSession, token_hash(user["token"]))
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.get("/me", headers=headers(user)).status_code == 401
    assert client.post("/auth/signup", json={"email": "other@example.com", "password": "я" * 40}).status_code == 422


@pytest.mark.parametrize("path", ["/me", "/me/profile", "/docs", "/overview", "/diagnosis"])
def test_auth_required(client, path):
    assert client.get(path).status_code == 401


def test_upload_import_and_ownership(client, grok):
    first = signup(client)
    second = signup(client, "other@example.com")
    auth = headers(first)
    original = image_bytes()
    response = client.post("/docs", headers=auth, files={"file": ("scan.png", original, "image/png")})
    assert response.status_code == 201, response.text
    document = response.json()
    url = f"/docs/{document['id']}"
    assert document["kind"] == "image"
    assert document["extracted"]["diagnoses"][0]["icd_10_code"] is None
    assert grok[0]["response_format"]["json_schema"]["schema"] == document_parser.response_schema()
    assert grok[0]["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert client.get(url, headers=auth).json() == document
    assert client.get(url + "/file", headers=auth).content == original
    assert client.get(url + "/file", headers=auth).headers["cache-control"] == "private, no-store"
    assert len(client.get("/docs", headers=auth).json()) == 1
    assert client.get(url, headers=headers(second)).status_code == 404
    assert client.get(url + "/file", headers=headers(second)).status_code == 404
    assert client.get(url + "/file").status_code == 401
    assert client.get("/docs", headers=headers(second)).json() == []
    assert client.get("/diagnosis", headers=headers(second)).json() is None
    assert len(client.get("/overview", headers=auth).json()) == 3
    assert client.post("/diagnosis", headers=auth).json()["findings"] == ["Recorded diagnosis (confirmed)"]
    with TestingSessionLocal() as db:
        for model in (Medication, Operation, Diagnosis):
            row = db.scalar(select(model))
            assert str(row.patient_id) == first["id"]
            assert str(row.source_document_id) == document["id"]
        assert db.scalar(select(Operation)).performed_at == "2020"
        assert db.scalar(select(Operation)).document_id is None
        assert db.scalar(select(Medication)).dosage == 5


def test_pdf_pages_and_original(client, grok):
    user = signup(client)
    output = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(output, format="PDF", save_all=True,
                                            append_images=[Image.new("RGB", (40, 40), "black")])
    content = output.getvalue()
    response = client.post("/docs", headers=headers(user), files={"file": ("scan.pdf", content, "application/pdf")})
    assert response.status_code == 201, response.text
    assert response.json()["kind"] == "pdf"
    assert len(grok[0]["messages"][1]["content"]) == 3
    assert client.get(response.json()["previewUrl"], headers=headers(user)).content == content


def test_upload_rejections(client, grok, monkeypatch):
    auth = headers(signup(client))
    for content, status in ((b"", 400), (b"not an image", 400), (b"%PDF-broken", 400)):
        assert client.post("/docs", headers=auth, files={"file": ("bad.png", content, "image/png")}).status_code == status
    monkeypatch.setattr(settings, "max_upload_bytes", 5)
    assert client.post("/docs", headers=auth, files={"file": ("large.png", image_bytes())}).status_code == 413
    assert not grok


def test_pdf_page_limit(monkeypatch):
    output = io.BytesIO()
    Image.new("RGB", (40, 40)).save(output, format="PDF", save_all=True,
                                   append_images=[Image.new("RGB", (40, 40))])
    monkeypatch.setattr(settings, "max_pdf_pages", 1)
    with pytest.raises(document_parser.InvalidDocument):
        prepare_images(output.getvalue())


@pytest.fixture
def context():
    return {"document_id": str(uuid4()), "patient_id": str(uuid4()),
            "s3_url": "https://example.org/document", "ingested_at": "2026-09-12T12:00:00+00:00"}


@pytest.mark.parametrize("mutation", [
    lambda d: d["patient"].update(id=str(uuid4())),
    lambda d: d["patient"].update(password_hash="injected"),
    lambda d: d["documents"][0].update(s3_url="https://other.example.org/file"),
    lambda d: d["medications"][0].update(patient_id=str(uuid4())),
    lambda d: d["medications"][0].update(doctor_id=str(uuid4())),
    lambda d: d["medications"].append(deepcopy(d["medications"][0])),
    lambda d: d["medical_visits"][0].update(diagnosis_ids=[str(uuid4())]),
    lambda d: d["operations"][0].update(performed_at="2026-02-30"),
])
def test_invalid_extractions(context, mutation):
    data = extraction(context)
    validate_extraction(data, context)
    mutation(data)
    with pytest.raises(ParserError):
        validate_extraction(data, context)


def test_invalid_output_leaves_no_rows(client, monkeypatch):
    auth = headers(signup(client))
    monkeypatch.setattr(settings, "xai_api_key", "test-key")
    monkeypatch.setattr("app.api.routes.history.parse_document", lambda *_: {"invalid": True})
    response = client.post("/docs", headers=auth, files={"file": ("scan.png", image_bytes())})
    assert response.status_code == 502
    with TestingSessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Document)) == 0
        assert db.scalar(select(func.count()).select_from(Medication)) == 0


def test_import_rolls_back_on_insert_failure(client, grok, monkeypatch):
    from app.services import document_import
    auth = headers(signup(client))
    original = document_import.model_values

    def broken_values(model, row):
        if model is Operation:
            raise RuntimeError("simulated database failure after medication insert")
        return original(model, row)

    monkeypatch.setattr(document_import, "model_values", broken_values)
    with pytest.raises(RuntimeError):
        client.post("/docs", headers=auth, files={"file": ("scan.png", image_bytes())})
    with TestingSessionLocal() as db:
        for table in document_import.MODELS.values():
            assert db.scalar(select(func.count()).select_from(table)) == 0
        assert db.scalar(select(func.count()).select_from(Document)) == 0


def test_missing_api_key(client, monkeypatch):
    monkeypatch.setattr(settings, "xai_api_key", "")
    auth = headers(signup(client))
    assert client.post("/docs", headers=auth, files={"file": ("scan.png", image_bytes())}).status_code == 503


@pytest.mark.parametrize("failure", ["timeout", "http", "json", "truncated", "refusal"])
def test_grok_failures(context, monkeypatch, failure):
    monkeypatch.setattr(settings, "xai_api_key", "test-key")
    original = httpx.Client

    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("timeout", request=request)
        if failure == "http":
            return httpx.Response(429, text="secret upstream details")
        if failure == "json":
            return httpx.Response(200, text="not JSON")
        return httpx.Response(200, json={"choices": [{"finish_reason": "length" if failure == "truncated" else "stop",
                                                     "message": {"content": "{}", "refusal": "refused"}}]})

    monkeypatch.setattr(document_parser.httpx, "Client", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    with pytest.raises(ParserError):
        document_parser.parse_document([], context)


def test_cors_and_render_database_url(client):
    response = client.options("/docs", headers={"Origin": "http://localhost:5173",
                              "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert Settings(database_url="postgres://u:p@db/name").database_url == "postgresql+psycopg2://u:p@db/name"

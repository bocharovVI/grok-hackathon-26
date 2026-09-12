from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import current_patient, session_user
from app.core.config import settings
from app.db.session import get_db
from app.models import Diagnosis, Document, Medication, Operation, Patient
from app.schemas.session import Profile, SessionUser
from app.services.document_import import import_document
from app.services.document_parser import InvalidDocument, ParserError, parse_document, prepare_images

router = APIRouter(tags=["history"])


@router.get("/me", response_model=SessionUser)
def me(patient: Patient = Depends(current_patient)) -> dict:
    return session_user(patient)


@router.get("/me/profile", response_model=Profile)
def profile(patient: Patient = Depends(current_patient)) -> dict:
    return patient.profile or Profile().model_dump()


@router.put("/me/profile", response_model=SessionUser)
def save_profile(payload: Profile, patient: Patient = Depends(current_patient),
                 db: Session = Depends(get_db)) -> dict:
    patient.profile = payload.model_dump()
    patient.height = round(float(payload.heightCm)) if payload.heightCm else None
    db.commit()
    return session_user(patient)


def doc_record(document: Document, include_extracted: bool = True) -> dict:
    return {
        "id": str(document.id), "title": document.filename,
        "kind": "pdf" if document.content_type == "application/pdf" else "image",
        "previewUrl": f"/docs/{document.id}/file",
        "extracted": document.extracted if include_extracted else {},
    }


def owned_document(document_id: UUID, patient: Patient, db: Session) -> Document:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.patient_id == patient.id))
    if document is None:
        raise HTTPException(404, "Document not found")
    return document


@router.get("/docs")
def list_documents(patient: Patient = Depends(current_patient), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Document).where(Document.patient_id == patient.id).order_by(Document.created_at.desc()))
    return [doc_record(row, include_extracted=False) for row in rows]


@router.get("/docs/{document_id}")
def get_document(document_id: UUID, patient: Patient = Depends(current_patient),
                 db: Session = Depends(get_db)) -> dict:
    return doc_record(owned_document(document_id, patient, db))


@router.get("/docs/{document_id}/file")
def get_document_file(document_id: UUID, patient: Patient = Depends(current_patient),
                      db: Session = Depends(get_db)) -> Response:
    document = owned_document(document_id, patient, db)
    return Response(document.content, media_type=document.content_type, headers={
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        "Content-Disposition": "inline",
    })


@router.post("/docs", status_code=201)
def upload_document(file: UploadFile, patient: Patient = Depends(current_patient),
                    db: Session = Depends(get_db)) -> dict:
    try:
        content = file.file.read(settings.max_upload_bytes + 1)
    finally:
        file.file.close()
    if not content:
        raise HTTPException(400, "The document is empty")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, f"Maximum upload size is {settings.max_upload_bytes // (1024 * 1024)} MiB")
    if not settings.xai_api_key:
        raise HTTPException(503, "Document parsing is not configured on the server")
    document_id = uuid4()
    context = {
        "document_id": str(document_id), "patient_id": str(patient.id),
        "s3_url": f"{settings.public_api_url.rstrip('/')}/docs/{document_id}/file",
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        content_type, images = prepare_images(content)
        data = parse_document(images, context)
        document = import_document(db, data, context, content, content_type, (file.filename or "document")[:255])
        db.commit()
    except InvalidDocument as exc:
        db.rollback()
        raise HTTPException(400, str(exc)) from None
    except ParserError as exc:
        db.rollback()
        raise HTTPException(502, str(exc)) from None
    except Exception:
        db.rollback()
        raise
    return doc_record(document)


@router.get("/overview")
def overview(patient: Patient = Depends(current_patient), db: Session = Depends(get_db)) -> list[str]:
    result = []
    for model, label in ((Diagnosis, "Diagnosis"), (Medication, "Medication"), (Operation, "Operation")):
        rows = db.scalars(select(model).where(model.patient_id == patient.id).order_by(model.created_at.desc()).limit(20))
        result.extend(f"{label}: {row.name}" for row in rows)
    return result or ["Upload a medical document to see extracted diagnoses, medications and operations."]


@router.get("/diagnosis")
@router.post("/diagnosis")
def diagnosis_summary(patient: Patient = Depends(current_patient), db: Session = Depends(get_db)) -> dict | None:
    rows = list(db.scalars(select(Diagnosis).where(Diagnosis.patient_id == patient.id).order_by(Diagnosis.created_at.desc())))
    if not rows:
        return None
    return {
        "id": str(patient.id), "title": "Diagnoses from your documents",
        "summary": "Only diagnoses explicitly recorded in uploaded documents are listed here.",
        "findings": [f"{row.name} ({row.status})" + (f" — {row.icd_10_code}" if row.icd_10_code else "") for row in rows],
    }

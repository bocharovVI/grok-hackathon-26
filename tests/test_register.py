from fastapi.testclient import TestClient


def _payload(**overrides: object) -> dict:
    data = {
        "email": "ivan@example.com",
        "password": "secret123",
        "first_name": "Ivan",
        "last_name": "Petrov",
        "phone_number": "+79991234567",
        "date_of_birth": "1990-05-15",
        "height": 180,
        "blood_type": 1,
    }
    data.update(overrides)
    return data


def test_register_patient_success(client: TestClient) -> None:
    response = client.post("/auth/register", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ivan@example.com"
    assert body["first_name"] == "Ivan"
    assert body["last_name"] == "Petrov"
    assert body["phone_number"] == "+79991234567"
    assert body["height"] == 180
    assert body["blood_type"] == 1
    assert "id" in body
    assert "created_at" in body
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    first = client.post("/auth/register", json=_payload())
    assert first.status_code == 201

    second = client.post(
        "/auth/register",
        json=_payload(email="Ivan@example.com", first_name="Other"),
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "Patient with this email already exists"

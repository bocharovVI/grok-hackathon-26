import hashlib
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AuthSession, Patient

bearer = HTTPBearer(auto_error=False)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> AuthSession:
    session = db.get(AuthSession, token_hash(credentials.credentials)) if credentials else None
    if session is None or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(401, "Sign in required", headers={"WWW-Authenticate": "Bearer"})
    return session


def current_patient(
    session: AuthSession = Depends(current_session), db: Session = Depends(get_db),
) -> Patient:
    patient = db.get(Patient, session.patient_id)
    if patient is None:
        raise HTTPException(401, "Sign in required")
    return patient


def session_user(patient: Patient) -> dict:
    profile = patient.profile or {}
    return {
        "id": str(patient.id), "email": patient.email,
        "profileComplete": all(profile.get(key) for key in ("heightCm", "weightKg", "age", "sex")),
    }

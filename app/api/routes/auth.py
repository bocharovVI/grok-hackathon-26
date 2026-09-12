import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import current_session, session_user, token_hash
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models import AuthSession
from app.models.patient import Patient
from app.schemas.patient import PatientRegisterRequest, PatientResponse
from app.schemas.session import Credentials, SessionResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_patient(
    payload: PatientRegisterRequest,
    db: Session = Depends(get_db),
) -> Patient:
    patient = Patient(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        phone_number=payload.phone_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        height=payload.height,
        blood_type=payload.blood_type,
    )
    db.add(patient)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient with this email already exists",
        ) from None
    db.refresh(patient)
    return patient


def issue_session(patient: Patient, db: Session) -> dict:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(
        token_hash=token_hash(token), patient_id=patient.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.session_days),
    ))
    db.commit()
    return {**session_user(patient), "token": token}


@router.post("/signup", response_model=SessionResponse, status_code=201)
def signup(payload: Credentials, db: Session = Depends(get_db)) -> dict:
    patient = Patient(
        email=str(payload.email).lower(), password_hash=hash_password(payload.password),
        first_name="", last_name="",
    )
    db.add(patient)
    try:
        db.flush()
        return issue_session(patient, db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Patient with this email already exists") from None


@router.post("/login", response_model=SessionResponse)
def login(payload: Credentials, db: Session = Depends(get_db)) -> dict:
    patient = db.scalar(select(Patient).where(Patient.email == str(payload.email).lower()))
    if patient is None or not verify_password(payload.password, patient.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    return issue_session(patient, db)


@router.post("/logout", status_code=204)
def logout(session: AuthSession = Depends(current_session), db: Session = Depends(get_db)) -> None:
    db.delete(session)
    db.commit()

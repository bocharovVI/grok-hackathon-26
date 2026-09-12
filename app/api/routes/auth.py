from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientRegisterRequest, PatientResponse

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

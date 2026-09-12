import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    type: Mapped[str] = mapped_column(Text)
    s3_url: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    extracted: Mapped[dict] = mapped_column(JSON)


class MedicalOrganization(Base):
    __tablename__ = "medical_organizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    full_name: Mapped[str] = mapped_column(Text)
    specialization: Mapped[str | None] = mapped_column(Text)
    med_org_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("medical_organizations.id"))


class ClinicalRecord:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("doctors.id"))
    med_org_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("medical_organizations.id"))
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id"))
    # Always retain import provenance, even for historical records with document_id=null.
    source_document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), index=True)
    created_at: Mapped[date] = mapped_column(Date)
    details: Mapped[dict] = mapped_column(JSON)


class Medication(ClinicalRecord, Base):
    __tablename__ = "medications"

    name: Mapped[str] = mapped_column(Text)
    dosage: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str | None] = mapped_column(Text)
    intake_conditions: Mapped[str | None] = mapped_column(Text)


class Operation(ClinicalRecord, Base):
    __tablename__ = "operations"

    type: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    performed_at: Mapped[str | None] = mapped_column(Text)


class Diagnosis(ClinicalRecord, Base):
    __tablename__ = "diagnoses"

    name: Mapped[str] = mapped_column(Text)
    icd_10_code: Mapped[str | None] = mapped_column(Text)
    diagnosis_type: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    diagnosed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Recommendation(ClinicalRecord, Base):
    __tablename__ = "recommendations"

    category: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)


class MedicalVisit(ClinicalRecord, Base):
    __tablename__ = "medical_visits"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    appointment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    visit_type: Mapped[str] = mapped_column(Text)

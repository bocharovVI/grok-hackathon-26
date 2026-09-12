from copy import deepcopy
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Uuid
from sqlalchemy.orm import Session

from app.models import (
    Diagnosis, Doctor, Document, MedicalOrganization, MedicalVisit, Medication,
    Operation, Recommendation,
)
from app.services.document_parser import validate_extraction

MODELS = {
    "medical_organizations": MedicalOrganization, "doctors": Doctor,
    "medications": Medication, "operations": Operation, "diagnoses": Diagnosis,
    "recommendations": Recommendation, "medical_visits": MedicalVisit,
}


def model_values(model, row: dict) -> dict:
    values = {}
    for column in model.__table__.columns:
        if column.name not in row:
            continue
        value = row[column.name]
        if value is not None:
            if isinstance(column.type, Uuid):
                value = UUID(value)
            elif isinstance(column.type, DateTime):
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            elif isinstance(column.type, Date):
                value = date.fromisoformat(value)
        values[column.name] = value
    return values


def import_document(db: Session, data: dict, context: dict, content: bytes,
                    content_type: str, filename: str) -> Document:
    validate_extraction(data, context)
    data = deepcopy(data)
    # LLM-generated IDs are local references, never authority to update existing rows.
    mapping = {row["id"]: str(uuid4()) for key in MODELS for row in data[key]}
    for key in MODELS:
        for row in data[key]:
            row["id"] = mapping[row["id"]]
            for fk in ("doctor_id", "med_org_id"):
                if row.get(fk):
                    row[fk] = mapping[row[fk]]
            for fk in ("diagnosis_ids", "recommendation_ids"):
                if fk in row:
                    row[fk] = [mapping[value] for value in row[fk]]
    document = Document(
        **model_values(Document, data["documents"][0]),
        patient_id=UUID(context["patient_id"]), filename=filename,
        content_type=content_type, content=content, extracted=data,
    )
    db.add(document)
    db.flush()
    for key, model in MODELS.items():
        for row in data[key]:
            values = model_values(model, row)
            if "patient_id" in row:
                values.update(source_document_id=document.id, details=row)
            db.add(model(**values))
        db.flush()
    # The caller commits once; failed validation/inserts leave no partial medical history.
    return document

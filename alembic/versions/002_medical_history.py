"""Document imports and frontend sessions.

Revision ID: 002_medical_history
Revises: 001_create_patients
"""
import sqlalchemy as sa
from alembic import op

revision = "002_medical_history"
down_revision = "001_create_patients"
branch_labels = None
depends_on = None


def clinical_columns(timestamp=False):
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("doctor_id", sa.Uuid(), sa.ForeignKey("doctors.id")),
        sa.Column("med_org_id", sa.Uuid(), sa.ForeignKey("medical_organizations.id")),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.id")),
        sa.Column("source_document_id", sa.Uuid(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True) if timestamp else sa.Date(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
    ]


def upgrade():
    op.add_column("patients", sa.Column("profile", sa.JSON(), nullable=True))
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_sessions_patient_id", "auth_sessions", ["patient_id"])
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("patient_id", sa.Uuid(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("s3_url", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("extracted", sa.JSON(), nullable=False),
    )
    op.create_index("ix_documents_patient_id", "documents", ["patient_id"])
    op.create_table(
        "medical_organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("city", sa.Text()),
    )
    op.create_table(
        "doctors",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("specialization", sa.Text()),
        sa.Column("med_org_id", sa.Uuid(), sa.ForeignKey("medical_organizations.id")),
    )
    op.create_table(
        "medications", *clinical_columns(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("dosage", sa.Float(), nullable=False),
        sa.Column("unit", sa.Text()),
        sa.Column("frequency", sa.Text()),
        sa.Column("intake_conditions", sa.Text()),
    )
    op.create_table(
        "operations", *clinical_columns(),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("performed_at", sa.Text()),
    )
    op.create_table(
        "diagnoses", *clinical_columns(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("icd_10_code", sa.Text()),
        sa.Column("diagnosis_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("diagnosed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "recommendations", *clinical_columns(),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
    )
    op.create_table(
        "medical_visits", *clinical_columns(timestamp=True),
        sa.Column("appointment_at", sa.DateTime(timezone=True)),
        sa.Column("visit_type", sa.Text(), nullable=False),
    )
    for table in ("medications", "operations", "diagnoses", "recommendations", "medical_visits"):
        op.create_index(f"ix_{table}_patient_id", table, ["patient_id"])
        op.create_index(f"ix_{table}_source_document_id", table, ["source_document_id"])


def downgrade():
    for table in ("medical_visits", "recommendations", "diagnoses", "operations", "medications",
                  "doctors", "medical_organizations", "documents", "auth_sessions"):
        op.drop_table(table)
    op.drop_column("patients", "profile")

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=32)
    date_of_birth: date | None = None
    height: int | None = Field(default=None, ge=1, le=300)
    blood_type: int | None = Field(default=None, ge=0, le=20)


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    phone_number: str | None
    first_name: str
    last_name: str
    date_of_birth: date | None
    height: int | None
    blood_type: int | None
    created_at: datetime

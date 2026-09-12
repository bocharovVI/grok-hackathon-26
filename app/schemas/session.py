import math
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.patient import PatientRegisterRequest


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_byte_length(cls, value: str) -> str:
        return PatientRegisterRequest.password_byte_length(value)


class Profile(BaseModel):
    heightCm: str = ""
    weightKg: str = ""
    age: str = ""
    sex: Literal["female", "male", "other", ""] = ""
    comments: str = Field(default="", max_length=10000)

    @field_validator("heightCm", "weightKg", "age")
    @classmethod
    def numeric_fields(cls, value: str, info) -> str:
        if value == "":
            return value
        number = float(value)
        lower, upper = {"heightCm": (1, 300), "weightKg": (1, 700), "age": (0, 130)}[info.field_name]
        if not math.isfinite(number) or not lower <= number <= upper:
            raise ValueError(f"{info.field_name} must be between {lower} and {upper}")
        return value


class SessionUser(BaseModel):
    id: str
    email: str
    profileComplete: bool


class SessionResponse(SessionUser):
    token: str

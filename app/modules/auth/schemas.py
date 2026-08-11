from enum import Enum

from pydantic import BaseModel, Field, EmailStr

class LoginRequest(BaseModel):
    document: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class BaseRegisterRequest(BaseModel):
    fullname: str
    email: EmailStr
    password : str

class DNIRegisterRequest(BaseRegisterRequest):
    dni: str = Field(..., min_length=8, max_length=8, pattern=r"^\d{8}$")

from pydantic import Field, field_validator

class ImmigrationCardRegisterRequest(BaseRegisterRequest):
    immigration_card: str = Field(
        ...,
        min_length=9,
        max_length=12
    )

    @field_validator("immigration_card")
    @classmethod
    def validate_format(cls, v):
        if not v.isalnum():
            raise ValueError("El carnet solo puede contener letras y números")
        return v

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    document_type: str
    document_number: str

    class Config:
        from_attributes = True

class UpdateEmailRequest(BaseModel):
    email: EmailStr
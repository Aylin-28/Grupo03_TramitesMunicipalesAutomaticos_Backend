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
    user_type : str

class DNIRegisterRequest(BaseRegisterRequest):
    dni: str = Field(..., min_length=8, max_length=8, pattern=r"^\d{8}$")

class ImmigrationCardRegisterRequest(BaseRegisterRequest):
    immigration_card: str = Field(
        ...,
        min_length=9,
        max_length=12,
        pattern=r"^[a-zA-Z0-9]+$"
    )
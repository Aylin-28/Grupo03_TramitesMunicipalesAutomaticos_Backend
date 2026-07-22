from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentObservedResponse(BaseModel):
    id: str
    chat_id: str
    filename: str
    extracted_text: str
    created_at: datetime
    chat_title: Optional[str] = None
    chat_state: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True

class DocumentUpdate(BaseModel):
    extracted_text: str

class ChatStateUpdate(BaseModel):
    state: str

class UserRoleUpdate(BaseModel):
    role: str

    class Config:
        json_schema_extra = {
            "example": {"role": "admin"}
        }


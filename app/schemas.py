from pydantic import BaseModel, Field
from datetime import datetime

class MessageCreate(BaseModel):
    room: str = Field(default="lobby", max_length=64)
    username: str = Field(..., max_length=64)
    text: str = Field(..., max_length=4096)

class MessageOut(BaseModel):
    id: int
    room: str
    username: str
    text: str
    created_at: datetime
    class Config:
        from_attributes = True

class AttachmentOut(BaseModel):
    id: int
    room: str
    username: str
    original_name: str
    stored_path: str
    mime_type: str
    size_bytes: int
    created_at: datetime
    url: str  # computed
    class Config:
        from_attributes = True

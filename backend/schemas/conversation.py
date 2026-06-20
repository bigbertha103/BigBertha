from typing import Optional
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationPatch(BaseModel):
    title: Optional[str] = None


class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: str
    updated_at: str


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    job_id: Optional[int]
    created_at: str



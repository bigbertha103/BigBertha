from pydantic import BaseModel


class PinnedCreate(BaseModel):
    content: str


class PinnedOut(BaseModel):
    id: int
    conversation_id: int
    content: str
    source: str
    job_id: int | None
    is_active: int
    created_at: str

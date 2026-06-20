from typing import Any, Optional
from pydantic import BaseModel


class JobStatusOut(BaseModel):
    id: int
    status: str
    agent_code: Optional[str] = None
    final_response: Optional[str] = None
    error_message: Optional[str] = None


class ConfigOut(BaseModel):
    model_config = {"extra": "allow"}


class ConfigUpdate(BaseModel):
    model_config = {"extra": "allow"}

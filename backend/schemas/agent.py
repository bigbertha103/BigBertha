from typing import Optional
from pydantic import BaseModel


class AgentOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str]
    is_active: int
    created_at: str


class CompanyProfileCreate(BaseModel):
    name: str
    sector: Optional[str] = None
    tone: Optional[str] = None
    business_rules: Optional[str] = None


class CompanyProfileOut(BaseModel):
    id: int
    name: str
    sector: Optional[str]
    tone: Optional[str]
    business_rules: Optional[str]
    updated_at: str

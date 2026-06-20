import logging

from fastapi import APIRouter, HTTPException

from backend.database import get_connection
from backend.schemas.agent import CompanyProfileCreate, CompanyProfileOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/company-profile", response_model=CompanyProfileOut)
def get_company_profile():
    db = get_connection()
    try:
        row = db.execute("SELECT * FROM company_profile WHERE id = 1").fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Profil entreprise non configuré")
        return dict(row)
    finally:
        db.close()


@router.put("/company-profile", response_model=CompanyProfileOut)
def upsert_company_profile(body: CompanyProfileCreate):
    db = get_connection()
    try:
        db.execute(
            """INSERT OR REPLACE INTO company_profile (id, name, sector, tone, business_rules, updated_at)
               VALUES (1, ?, ?, ?, ?, datetime('now'))""",
            (body.name, body.sector, body.tone, body.business_rules),
        )
        db.commit()
        row = db.execute("SELECT * FROM company_profile WHERE id = 1").fetchone()
        return dict(row)
    finally:
        db.close()

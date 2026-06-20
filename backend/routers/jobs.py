import json
import logging

from fastapi import APIRouter, HTTPException

from backend.database import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job(job_id: int):
    db = get_connection()
    try:
        job = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if job is None:
            raise HTTPException(status_code=404, detail="Job introuvable")

        job = dict(job)
        status = job["status"]

        if status in ("PENDING", "ROUTING"):
            return {"id": job["id"], "status": status}

        if status in ("AGENT_RUNNING", "SYNTHESIZING"):
            agent_code = None
            if job.get("routing_output"):
                try:
                    routing = json.loads(job["routing_output"])
                    agent_code = routing.get("agent_code")
                except (json.JSONDecodeError, KeyError):
                    pass
            return {"id": job["id"], "status": status, "agent_code": agent_code}

        if status == "DONE":
            agent_code = None
            if job.get("routing_output"):
                try:
                    routing = json.loads(job["routing_output"])
                    agent_code = routing.get("agent_code")
                except (json.JSONDecodeError, KeyError):
                    pass
            return {
                "id": job["id"],
                "status": status,
                "final_response": job.get("final_response"),
                "agent_code": agent_code,
            }

        if status == "ERROR":
            return {
                "id": job["id"],
                "status": status,
                "error_message": job.get("error_message"),
            }

        return {"id": job["id"], "status": status}
    finally:
        db.close()

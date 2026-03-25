from fastapi import FastAPI # type: ignore
from pydantic import BaseModel # type: ignore
import uuid

from app.db import SessionLocal, engine, Base
from app.models.job import Job
from app.jobs.queue import enqueue_job

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class Repo(BaseModel):
    full_name: str

class WebhookPayload(BaseModel):
    repository: Repo
    ref: str
    after: str

# Webhook endpoint
@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload):
    db = SessionLocal()

    job = Job(
        id=str(uuid.uuid4()),
        repo=payload.repository.full_name,
        branch=payload.ref,
        commit_sha=payload.after,
        status="queued"
    )

    db.add(job)
    db.commit()

    enqueue_job(job.id)
    
    return {"job_id": job.id}

@app.get("/jobs")
def get_jobs():
    db = SessionLocal()
    jobs = db.query(Job).all()

    return [
        {
            "id": j.id,
            "repo": j.repo,
            "status": j.status,
            "current_stage": j.current_stage
        }
        for j in jobs
    ]


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        return {"error": "Job not found"}

    return {
        "id": job.id,
        "repo": job.repo,
        "status": job.status,
        "current_stage": job.current_stage,
        "stages": job.stages
    }
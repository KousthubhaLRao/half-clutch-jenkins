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
    
    
from fastapi.responses import HTMLResponse

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    db = SessionLocal()
    jobs = db.query(Job).all()

    queued = [j for j in jobs if j.status == "queued"]
    running = [j for j in jobs if j.status == "running"]
    completed = [j for j in jobs if j.status == "completed"]

    def job_card(j):
        stages_html = ""
        if j.stages:
            for stage, state in j.stages.items():
                color = {"pending": "#888", "running": "#f0a500", "completed": "#4caf50"}.get(state, "#888")
                stages_html += f'<span style="background:{color};padding:3px 8px;border-radius:4px;margin:2px;display:inline-block">{stage}: {state}</span>'
        return f"""
        <div style="border:1px solid #444;padding:12px;margin:8px 0;border-radius:6px;background:#1e1e1e">
            <b>{j.repo}</b> — branch: {j.branch}<br>
            <small>commit: {j.commit_sha[:7] if j.commit_sha else ''}</small><br>
            <small>id: {j.id}</small><br>
            <div style="margin-top:8px">{stages_html}</div>
        </div>"""

    def column(title, color, job_list):
        cards = "".join(job_card(j) for j in job_list)
        return f"""
        <div style="flex:1;padding:12px">
            <h2 style="color:{color};border-bottom:2px solid {color};padding-bottom:6px">{title} ({len(job_list)})</h2>
            {cards if cards else '<p style="color:#666">None</p>'}
        </div>"""

    body = f"""
    <html>
    <head>
        <title>Half Clutch Jenkins</title>
        <meta http-equiv="refresh" content="3">
        <style>body{{background:#121212;color:#eee;font-family:sans-serif;margin:0;padding:20px}}</style>
    </head>
    <body>
        <h1>Half Clutch Jenkins Dashboard</h1>
        <p style="color:#888">Auto-refreshes every 3 seconds</p>
        <div style="display:flex;gap:16px">
            {column("Queued", "#2196f3", queued)}
            {column("In Progress", "#f0a500", running)}
            {column("Completed", "#4caf50", completed)}
        </div>
    </body>
    </html>"""

    return body

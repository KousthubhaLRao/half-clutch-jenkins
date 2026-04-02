from fastapi import FastAPI, Depends, HTTPException 
from fastapi.responses import HTMLResponse
from pydantic import BaseModel 
from sqlalchemy.orm import Session
import uuid
import random
import requests

from app.db import SessionLocal, engine, Base 
from app.models.job import Job 
from app.jobs.queue import enqueue_job 

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine) 

# Dependency to get DB session and ensure it closes after the request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
class Repo(BaseModel):
    full_name: str

class WebhookPayload(BaseModel):
    repository: Repo
    ref: str
    after: str

@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    # 1. Detect Language via GitHub API
    lang_resp = requests.get(f"https://api.github.com/repos/{payload.repository.full_name}/languages")
    languages = lang_resp.json() if lang_resp.status_code == 200 else {"Python": 100}
    primary_lang = max(languages, key=languages.get) if languages else "Python"

    # 2. Create the Job with ALL required fields
    job = Job(
        id=str(uuid.uuid4()),
        repo=payload.repository.full_name,
        branch=payload.ref,           
        commit_sha=payload.after,      
        language=primary_lang,        
        priority=random.randint(1, 5), # High priority is 5
        status="queued"
    )

    db.add(job)
    db.commit()
    db.refresh(job) 

    # 3. Add to Queue with Priority
    enqueue_job(job.id, job.priority) 
    
    return {"job_id": job.id}

@app.get("/jobs")
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    return [
        {
            "id": j.id, 
            "repo": j.repo, 
            "status": j.status, 
            "language": j.language,
            "priority": j.priority,
            "worker_id": j.worker_id
        }
        for j in jobs
    ]

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(db: Session = Depends(get_db)):
    jobs = db.query(Job).all() 

    queued = [j for j in jobs if j.status == "queued"]
    running = [j for j in jobs if j.status == "running"]
    completed = [j for j in jobs if j.status == "completed"]

    def job_card(j):
        stages_html = ""
        current_stages = j.stages if j.stages else {} 
        
        # Priority Stars visualization
        priority_stars = "⭐" * (j.priority if j.priority else 1)
        
        for stage, state in current_stages.items():
            # Harvest-themed stage colors
            color = {"pending": "#8d6e63", "running": "#f0a500", "completed": "#4caf50"}.get(state, "#8d6e63")
            stages_html += f'<span style="background:{color};color:white;padding:3px 8px;border-radius:12px;margin:2px;display:inline-block;font-size:10px">{stage}</span>'
        
        return f"""
        <div style="border:1px solid #d7ccc8;padding:15px;margin:10px 0;border-radius:4px;background:#fff;box-shadow:3px 3px 0px #bcaaa4">
            <b style="color:#3e2723">{j.repo}</b> <small style="color:#8d6e63">({j.language})</small><br>
            <div style="margin:5px 0">Priority: {priority_stars}</div>
            <small style="color:#a1887f">Worker: {j.worker_id if j.worker_id else 'None'}</small><br>
            <small>commit: {j.commit_sha[:7] if j.commit_sha else 'N/A'}</small><br>
            <div style="margin-top:8px">{stages_html}</div>
        </div>"""

    def column(title, jobs_list):
        cards = "".join(job_card(j) for j in jobs_list)
        return f"""
        <div style="flex:1;padding:15px;background:#efebe9;margin:10px;border-radius:8px;border:1px solid #d7ccc8">
            <h2 style="color:#5d4037;border-bottom:2px solid #8d6e63;padding-bottom:10px">{title} ({len(jobs_list)})</h2>
            {cards if cards else '<p style="color:#bcaaa4">No bales in this field...</p>'}
        </div>"""

    return f"""
    <html>
    <head>
        <title>The Loom - Harvest Dashboard</title>
        <meta http-equiv="refresh" content="3">
        <style>
            body {{
                background-color: #fdf5e6; 
                color: #5d4037; 
                font-family: 'Courier New', Courier, monospace; 
                margin: 0; 
                padding: 20px;
            }}
            h1 {{
                text-align: center;
                text-transform: uppercase;
                letter-spacing: 5px;
                color: #3e2723;
                border-bottom: 4px double #8d6e63;
                padding-bottom: 10px;
                margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>
        <h1>🌾 The Loom Harvest Dashboard</h1>
        <p style="text-align:center;color:#8d6e63;margin-top:-20px">Monitoring the progress of your cotton pickers...</p>
        <div style="display:flex;gap:10px;max-width:1200px;margin:0 auto">
            {column("Awaiting Collection", queued)}
            {column("In the Gin (Running)", running)}
            {column("Baled & Ready (Done)", completed)}
        </div>
    </body>
    </html>"""
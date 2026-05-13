from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Depends, HTTPException 
from fastapi.responses import HTMLResponse
from pydantic import BaseModel 
from sqlalchemy.orm import Session
import uuid
import requests

from app.db import SessionLocal, engine, Base 
from app.models.job import Job 
from app.jobs.queue import enqueue_job 

app = FastAPI()

# Mount the static folder for background image
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create tables
Base.metadata.create_all(bind=engine) 

# Dependency to get DB session
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

# NEW: Strategic Priority Logic based on 6-branch simulation
def calculate_priority(ref: str) -> int:
    """
    Priority 3: Main/Master (Production)
    Priority 2: Staging/Develop (Testing)
    Priority 1: All other feature branches
    """
    ref = ref.lower()
    if "main" in ref or "master" in ref:
        return 3
    elif "staging" in ref or "develop" in ref:
        return 2
    else:
        return 1

@app.post("/webhook")
async def receive_webhook(payload: WebhookPayload, db: Session = Depends(get_db)):
    # 0. Deduplication Check: Don't process the same commit twice
    existing_job = db.query(Job).filter(
    Job.commit_sha == payload.after,
    Job.status.in_(["queued", "running"])
).first()
    if existing_job:
        print(f"♻️ Skipping duplicate commit: {payload.after[:7]}")
        return {"status": "skipped", "reason": "duplicate commit"}

    # 1. Detect Language via GitHub API
    headers = {"Authorization": "token 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"}
    url = f"https://api.github.com/repos/{payload.repository.full_name}/languages"
    
    try:
        lang_resp = requests.get(url, headers=headers, timeout=5)
        if lang_resp.status_code == 200:
            languages = lang_resp.json()
            primary_lang = max(languages, key=languages.get) if languages else "Generic"
        else:
            primary_lang = "Python"
    except Exception:
        primary_lang = "Python"

    # 2. Assign Priority based on Branch
    assigned_priority = calculate_priority(payload.ref)

    # 3. Create the Job
    job = Job(
        id=str(uuid.uuid4()),
        repo=payload.repository.full_name,
        branch=payload.ref,           
        commit_sha=payload.after,      
        language=primary_lang,        
        priority=assigned_priority, # Now using calculated 1, 2, or 3
        status="queued"
    )

    db.add(job)
    db.commit()
    db.refresh(job) 

    # 4. Add to Redis Priority Queue (ZADD happens inside enqueue_job)
    enqueue_job(job.id, job.priority) 
    
    print(f"🚀 Job {job.id[:8]} Enqueued | Branch: {payload.ref} | Priority: {job.priority}")
    return {"job_id": job.id, "priority": job.priority}

@app.get("/jobs")
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.priority.desc()).all()
    return jobs

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(db: Session = Depends(get_db)):
    # Sort by priority desc so the highest priority shows at the top of the columns
    jobs = db.query(Job).order_by(Job.priority.desc()).all() 

    queued = [j for j in jobs if j.status == "queued"]
    running = [j for j in jobs if j.status == "running"]
    completed = [j for j in jobs if j.status == "completed"]

    def job_card(j):
        stages_html = ""
        current_stages = j.stages if j.stages else {} 
        
        # Visual Priority Indicator (3 stars max)
        priority_label = {3: "🔴 HIGH (P3)", 2: "🟡 MID (P2)", 1: "🔵 LOW (P1)"}.get(j.priority, "LOW")
        stars = "⭐" * j.priority
        
        for stage, state in current_stages.items():
            color = {"pending": "#8d6e63", "running": "#f0a500", "completed": "#4caf50"}.get(state, "#8d6e63")
            stages_html += f'<span style="background:{color};color:white;padding:3px 8px;border-radius:12px;margin:2px;display:inline-block;font-size:10px">{stage}</span>'
        
        return f"""
        <div class="job-card">
            <b style="color:#3e2723">{j.repo}</b> <small style="color:#8d6e63">({j.language})</small><br>
            <div style="margin:5px 0; font-size: 12px; font-weight: bold;">{priority_label} {stars}</div>
            <small style="color:#a1887f">Branch: {j.branch.split('/')[-1]}</small><br>
            <small>SHA: {j.commit_sha[:7] if j.commit_sha else 'N/A'}</small><br>
            <div style="margin-top:8px">{stages_html}</div>
        </div>"""

    def column(title, jobs_list):
        cards = "".join(job_card(j) for j in jobs_list)
        return f"""
        <div class="column">
            <h2>{title} ({len(jobs_list)})</h2>
            {cards if cards else '<p style="color:#bcaaa4">Waiting for seeds...</p>'}
        </div>"""

    # ... (Keep the rest of your existing Dashboard HTML/CSS style block same as before)
    return f"""
    <html>
    <head>
        <title>The Loom - Harvest Dashboard</title>
        <meta http-equiv="refresh" content="3">
        <style>
            body {{
                background: linear-gradient(rgba(253, 245, 230, 0.2), rgba(253, 245, 230, 0.2)), 
                            url('/static/background.jpg');
                background-size: cover; 
                background-attachment: fixed;
                color: #5d4037; 
                font-family: 'Courier New', Courier, monospace; 
                margin: 0; 
                padding: 20px;
            }}
            h1 {{
                text-align: center;
                background: rgba(253, 245, 230, 0.9);
                display: table;
                margin: 0 auto 30px auto;
                padding: 10px 40px;
                border: 4px double #8d6e63;
            }}
            .column {{ flex: 1; padding: 15px; background: rgba(239, 235, 233, 0.9); margin: 10px; border-radius: 8px; backdrop-filter: blur(5px); border: 1px solid #d7ccc8; }}
            .job-card {{ border: 1px solid #d7ccc8; padding: 15px; margin: 10px 0; border-radius: 4px; background: #fff; box-shadow: 3px 3px 0px #bcaaa4; }}
        </style>
    </head>
    <body>
        <h1>🌾 The Loom Harvest Dashboard</h1>
        <div style="display:flex;gap:10px;max-width:1200px;margin:0 auto">
            {column("Queue (Priority Order)", queued)}
            {column("Worker Processing", running)}
            {column("Finished Bales", completed)}
        </div>
    </body>
    </html>"""
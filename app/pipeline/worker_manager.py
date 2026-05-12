import time
import re
import requests
import threading
import random
from app.jobs.queue import r
from app.db import SessionLocal
from app.models.job import Job

# 1. The Expert Harvester Class
class Harvester:
    def __init__(self, name, specialty):
        self.name = name
        self.specialty = specialty
        self.busy = False

    def process_job(self, job_id, priority_score):
        self.busy = True
        db = SessionLocal()
        
        # Ensure job_id is a clean string (Fixes byte-string issues)
        clean_id = job_id.decode('utf-8') if isinstance(job_id, bytes) else job_id
        
        job = db.query(Job).filter(Job.id == clean_id).first()
        
        if not job:
            print(f"[{self.name}] ❌ Error: Job {clean_id} not found in DB.")
            self.busy = False
            db.close()
            return

        priority_label = {3: "HIGH (P3)", 2: "MID (P2)", 1: "LOW (P1)"}.get(priority_score, "LOW")
        print(f"[{self.name}] 🚜 Harvesting {priority_label} job: {job.repo} on {job.branch}")
        
        job.status = "running"
        job.worker_id = self.name
        db.commit()

        # Parsing Jenkinsfile
        stages = self.fetch_jenkinsfile_stages(job.repo, job.branch)
        job.stages = {s: "pending" for s in stages}
        db.commit()

        for stage in stages:
            print(f"[{self.name}] Stage: {stage}...")
            job.current_stage = stage
            
            # Atomic update of the JSONB field
            current_stages = dict(job.stages)
            current_stages[stage] = "running"
            job.stages = current_stages
            db.commit()
            
            # Simulate build time
            time.sleep(random.uniform(3, 7)) 
            
            current_stages[stage] = "completed"
            job.stages = current_stages
            db.commit()

        print(f"[{self.name}] ✅ Job {clean_id[:8]} Baled & Ready.")
        job.status = "completed"
        job.current_stage = None
        db.commit()
        db.close()
        self.busy = False

    def fetch_jenkinsfile_stages(self, repo, branch):
        # Clean branch name
        branch_name = branch.split('/')[-1]
        url = f"https://raw.githubusercontent.com/{repo}/{branch_name}/Jenkinsfile"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                stages = re.findall(r"stage\(['\"](.+?)['\"]\)", response.text)
                if stages: return stages
        except Exception:
            pass
        
        return ["Fetch", "Build", "Test", "Deploy"]

# 2. The Worker Crew
crew = [
    Harvester("Python-Harvester-1", "Python"),
    Harvester("Python-Harvester-2", "Python"),
    Harvester("JS-Harvester", "JavaScript"),
    Harvester("CPP-Harvester", "C++"),
    Harvester("General-Laborer", "Generic")
]

def run_manager():
    print("\n" + "="*50)
    print("🌾 WORK MANAGER STARTING...")
    print("DEMO MODE: Pausing for 5 seconds to let the queue fill...")
    print("="*50 + "\n")
    
    # This delay allows you to "clog" the queue before workers start picking
    time.sleep(5) 
    
    print("🚜 Harvesters are entering the fields now!\n")

    while True:
        # ZPOPMAX ensures we get the HIGHEST priority (P3 > P2 > P1)
        job_data = r.zpopmax("job_priority_queue")
        
        if job_data:
            job_id, priority = job_data[0] # job_id is bytes, priority is float
            
            db = SessionLocal()
            clean_id = job_id.decode('utf-8') if isinstance(job_id, bytes) else job_id
            job = db.query(Job).filter(Job.id == clean_id).first()
            
            if not job:
                db.close()
                continue
            
            assigned = False
            
            # Try specialists first
            for worker in crew:
                if not worker.busy and worker.specialty == job.language:
                    threading.Thread(target=worker.process_job, args=(job_id, priority)).start()
                    assigned = True
                    break
            
            # Fallback to General Laborer
            if not assigned:
                for worker in crew:
                    if not worker.busy and worker.specialty == "Generic":
                        threading.Thread(target=worker.process_job, args=(job_id, priority)).start()
                        assigned = True
                        break
            
            # If no worker is free, put it back
            if not assigned:
                r.zadd("job_priority_queue", {job_id: priority})
            
            db.close()
            
        time.sleep(0.5) # Fast polling for responsiveness

if __name__ == "__main__":
    run_manager()
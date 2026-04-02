import time
import re
import requests
import threading
import random
from app.jobs.queue import r
from app.db import SessionLocal
from app.models.job import Job

# 1. The Expert Worker (Harvester) Class
class Harvester:
    def __init__(self, name, specialty):
        self.name = name
        self.specialty = specialty
        self.busy = False

    def process_job(self, job_id):
        self.busy = True
        db = SessionLocal()
        job = db.query(Job).filter(Job.id == job_id).first()
        
        if not job:
            self.busy = False
            db.close()
            return

        print(f"[{self.name}] Started harvesting {job.repo} (Language: {job.language})")
        job.status = "running"
        job.worker_id = self.name #
        db.commit()

        # Fetch stages directly from Jenkinsfile using Regex
        stages = self.fetch_jenkinsfile_stages(job.repo, job.branch)
        job.stages = {s: "pending" for s in stages} #
        db.commit()

        for stage in stages:
            print(f"[{self.name}] Running stage: {stage}")
            job.current_stage = stage #
            
            # Update stage status to running
            job.stages = {**job.stages, stage: "running"}
            db.commit()
            
            # Simulate real-world behavior with randomness
            time.sleep(random.uniform(2, 5)) 
            
            # Update stage status to completed
            job.stages = {**job.stages, stage: "completed"}
            db.commit()

        print(f"[{self.name}] Job {job_id} completed successfully.")
        job.status = "completed"
        job.current_stage = None
        db.commit()
        db.close()
        self.busy = False

    def fetch_jenkinsfile_stages(self, repo, branch):
        # Clean up branch name for the URL
        branch = branch.replace("refs/heads/", "")
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/Jenkinsfile"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Extract stage names using the regex for Groovy Jenkinsfiles
                stages = re.findall(r"stage\(['\"](.+?)['\"]\)", response.text)
                if stages:
                    return stages
        except Exception as e:
            print(f"[{self.name}] Could not fetch Jenkinsfile: {e}")
        
        # Fallback if no Jenkinsfile is found or parsing fails
        return ["checkout", "build", "test"]

# 2. Initialize the Crew (5 Workers)
crew = [
    Harvester("Python-Harvester-1", "Python"),
    Harvester("Python-Harvester-2", "Python"),
    Harvester("JS-Harvester", "JavaScript"),
    Harvester("CPP-Harvester", "C++"),
    Harvester("General-Laborer", "Generic")
]

def run_manager():
    print("🌾 Work Manager is patrolling the fields...")
    
    while True:
        # Priority Scheduling: Pick highest priority job from Redis Sorted Set
        job_data = r.zpopmax("job_priority_queue")
        
        if job_data:
            # Redis zpopmax returns a list of tuples: [(member, score)]
            job_id, priority = job_data[0]
            
            db = SessionLocal()
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                db.close()
                continue
            
            assigned = False
            
            # Step 1: Try to find a specialist for the language
            for worker in crew:
                if not worker.busy and worker.specialty == job.language:
                    threading.Thread(target=worker.process_job, args=(job_id,)).start()
                    assigned = True
                    break
            
            # Step 2: Fallback to the Generic worker if no specialist is free
            if not assigned:
                for worker in crew:
                    if not worker.busy and worker.specialty == "Generic":
                        threading.Thread(target=worker.process_job, args=(job_id,)).start()
                        assigned = True
                        break
            
            # Step 3: If everyone is busy, put the job back in the queue
            if not assigned:
                r.zadd("job_priority_queue", {job_id: priority})
            
            db.close()
            
        time.sleep(1)

if __name__ == "__main__":
    run_manager()
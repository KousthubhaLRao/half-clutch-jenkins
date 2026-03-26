import time
import re
import requests

from app.jobs.queue import r
from app.db import SessionLocal
from app.models.job import Job


def fetch_jenkinsfile_stages(repo, branch):
    # Clean up branch name (refs/heads/main -> main)
    branch = branch.replace("refs/heads/", "")
    
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/Jenkinsfile"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            # Extract stage names using regex
            stages = re.findall(r"stage\(['\"](.+?)['\"]\)", content)
            if stages:
                return stages
    except Exception as e:
        print(f"Could not fetch Jenkinsfile: {e}")
    
    # Fallback if no Jenkinsfile found
    return ["checkout", "build", "test"]


def run_pipeline():
    print("Pipeline executor started...")

    while True:
        result = r.brpop("job_queue", timeout=5)

        if result:
            _, job_id = result

            db = SessionLocal()
            job = db.query(Job).filter(Job.id == job_id).first()

            if not job:
                continue

            print(f"\nRunning job: {job_id}")
            print(f"Fetching Jenkinsfile from {job.repo} on branch {job.branch}")

            # Fetch real stages from Jenkinsfile
            stages = fetch_jenkinsfile_stages(job.repo, job.branch)
            print(f"Stages found: {stages}")

            job.status = "running"
            job.stages = {s: "pending" for s in stages}
            db.commit()

            for stage in stages:
                print(f"Running stage: {stage}")
                job.current_stage = stage
                
                # Mark this stage as running
                job.stages = {**job.stages, stage: "running"}
                db.commit()

                time.sleep(2)  # Simulate stage execution

                # Mark this stage as completed
                job.stages = {**job.stages, stage: "completed"}
                db.commit()

            print("Job completed")
            job.status = "completed"
            job.current_stage = None
            db.commit()

        time.sleep(1)


if __name__ == "__main__":
    run_pipeline()
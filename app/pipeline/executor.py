import time

from app.jobs.queue import r
from app.db import SessionLocal
from app.models.job import Job


def run_pipeline():
    print("Pipeline executor started...")

    while True:
        result = r.brpop("job_queue", timeout=5)

        if result:
            _, job_id = result  # FIX: brpop returns (key, value)

            db = SessionLocal()
            job = db.query(Job).filter(Job.id == job_id).first()

            if not job:
                continue

            print(f"\nRunning job: {job_id}")

            job.status = "running"

            # Define pipeline stages
            stages = ["checkout", "build", "test"]

            job.stages = stages
            db.commit()

            for stage in stages:
                job.current_stage = stage
                db.commit()

                print(f"Running stage: {stage}")

                time.sleep(2)

            print("Job completed")

            job.status = "completed"
            job.current_stage = None
            db.commit()

        time.sleep(1)


if __name__ == "__main__":
    run_pipeline()
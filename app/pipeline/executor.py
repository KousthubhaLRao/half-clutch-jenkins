import time

from app.jobs.queue import r
from app.db import SessionLocal
from app.models.job import Job


def run_pipeline():
    print("Pipeline executor started...")

    while True:
        job_id = r.brpop("job_queue", timeout=5)

        if job_id:
            db = SessionLocal()
            job = db.query(Job).filter(Job.id == job_id).first()

            if not job:
                continue

            print(f"\n🚀 Running job: {job_id}")

            job.status = "running"
            db.commit()

            # Simulated pipeline stages
            print("📦 Cloning repo...")
            time.sleep(2)

            print("🔨 Building...")
            time.sleep(2)

            print("🧪 Testing...")
            time.sleep(2)

            print("✅ Job completed")

            job.status = "completed"
            db.commit()

        time.sleep(1)


if __name__ == "__main__":
    run_pipeline()
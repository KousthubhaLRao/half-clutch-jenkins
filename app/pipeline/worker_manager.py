

import os
import re
import shutil
import threading
import time
import random
import datetime
import requests

from app.jobs.queue import r
from app.db import SessionLocal
from app.models.job import Job

# ── Constants ──────────────────────────────────────────────────────────────────
STAGE_TIMEOUT_SEC   = 600   # 10 minutes per stage
PIPELINE_TIMEOUT_SEC = 1800  # 30 minutes total
HEARTBEAT_INTERVAL  = 10    # seconds between heartbeat writes
REAPER_INTERVAL     = 30    # seconds between reaper scans
ORPHAN_THRESHOLD    = 120   # seconds without heartbeat → consider worker dead
WORKSPACE_ROOT      = "/tmp/half-clutch/workspaces"
GITHUB_TOKEN        = os.environ.get("GITHUB_TOKEN", "")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_workspace(job_id: str) -> str:
    path = os.path.join(WORKSPACE_ROOT, job_id)
    os.makedirs(path, exist_ok=True)
    return path


def _cleanup_workspace(job_id: str):
    path = os.path.join(WORKSPACE_ROOT, job_id)
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def _fetch_jenkinsfile_with_retry(repo: str, branch: str, max_attempts: int = 3):
    """Fetch Jenkinsfile from GitHub with exponential back-off retry."""
    branch_name = branch.split("/")[-1]
    url = f"https://raw.githubusercontent.com/{repo}/{branch_name}/Jenkinsfile"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                stages = re.findall(r"stage\(['\"](.+?)['\"]\)", resp.text)
                if stages:
                    print(f"   📄 Jenkinsfile parsed: {stages}")
                    return stages
        except Exception as exc:
            print(f"   ⚠️  Fetch attempt {attempt} failed: {exc}")

        if attempt < max_attempts:
            wait = 2 ** attempt          # 2s, 4s
            print(f"   ⏳ Retrying in {wait}s …")
            time.sleep(wait)

    print("   ⚠️  Jenkinsfile unavailable — using default stages")
    return ["Fetch", "Build", "Test", "Deploy"]


# ── Harvester ──────────────────────────────────────────────────────────────────

class Harvester:
    def __init__(self, name: str, specialty: str):
        self.name      = name
        self.specialty = specialty
        self.busy      = False

    # ── public entry point (run in its own thread) ──────────────────────────
    def process_job(self, job_id, priority_score):
        self.busy = True
        clean_id  = job_id.decode("utf-8") if isinstance(job_id, bytes) else job_id
        db        = SessionLocal()

        try:
            job = db.query(Job).filter(Job.id == clean_id).first()
            if not job:
                print(f"[{self.name}] ❌ Job {clean_id[:8]} not found in DB.")
                return

            priority_label = {3: "HIGH (P3)", 2: "MID (P2)", 1: "LOW (P1)"}.get(
                int(priority_score), "LOW"
            )
            print(f"[{self.name}] 🚜 Harvesting {priority_label}: {job.repo} @ {job.branch}")

            # ── Mark job as running ─────────────────────────────────────────
            job.status         = "running"
            job.worker_id      = self.name
            job.last_heartbeat = datetime.datetime.utcnow()
            db.commit()

            # ── Set up isolated workspace ───────────────────────────────────
            workspace = _make_workspace(clean_id)
            print(f"[{self.name}] 📁 Workspace: {workspace}")

            # ── Fetch & parse Jenkinsfile ───────────────────────────────────
            stages = _fetch_jenkinsfile_with_retry(job.repo, job.branch)
            job.stages = {s: "pending" for s in stages}
            db.commit()

            # ── Execute stages sequentially ─────────────────────────────────
            pipeline_start  = time.time()
            pipeline_failed = False

            for stage in stages:
                # ── Global pipeline timeout ─────────────────────────────────
                if time.time() - pipeline_start > PIPELINE_TIMEOUT_SEC:
                    print(f"[{self.name}] ⏰ Global pipeline timeout reached!")
                    self._fail_job(db, job, stage, "Pipeline global timeout exceeded")
                    pipeline_failed = True
                    break

                print(f"[{self.name}] ▶️  Stage: {stage}")
                job.current_stage  = stage
                current_stages     = dict(job.stages)
                current_stages[stage] = "running"
                job.stages         = current_stages
                job.last_heartbeat = datetime.datetime.utcnow()
                db.commit()

                # ── Simulate stage execution with heartbeat + timeout ────────
                stage_start    = time.time()
                stage_duration = random.uniform(3, 7)   # simulated work
                stage_failed   = False

                while time.time() - stage_start < stage_duration:
                    # Heartbeat ping
                    if time.time() - stage_start > 0 and \
                            int(time.time() - stage_start) % HEARTBEAT_INTERVAL == 0:
                        job.last_heartbeat = datetime.datetime.utcnow()
                        db.commit()

                    # Stage-level timeout guard
                    if time.time() - stage_start > STAGE_TIMEOUT_SEC:
                        print(f"[{self.name}] ⏰ Stage '{stage}' timed out!")
                        stage_failed = True
                        break

                    time.sleep(0.5)

                if stage_failed:
                    self._fail_job(db, job, stage, f"Stage '{stage}' timed out")
                    pipeline_failed = True
                    break

                # ── Stage completed ─────────────────────────────────────────
                current_stages        = dict(job.stages)
                current_stages[stage] = "completed"
                job.stages            = current_stages
                job.last_heartbeat    = datetime.datetime.utcnow()
                db.commit()
                print(f"[{self.name}] ✅ Stage '{stage}' done.")

            # ── Pipeline finished ───────────────────────────────────────────
            if not pipeline_failed:
                job.status        = "completed"
                job.current_stage = None
                db.commit()
                print(f"[{self.name}] 🏆 Job {clean_id[:8]} COMPLETED.")

        except Exception as exc:
            print(f"[{self.name}] 💥 Unexpected error: {exc}")
            try:
                job.status = "failed"
                db.commit()
            except Exception:
                pass

        finally:
            db.close()
            _cleanup_workspace(clean_id)
            self.busy = False

    # ── helpers ─────────────────────────────────────────────────────────────
    def _fail_job(self, db, job, failed_stage: str, reason: str):
        """Mark the current stage and overall job as failed (fail-fast)."""
        print(f"[{self.name}] ❌ FAILED at stage '{failed_stage}': {reason}")
        current_stages = dict(job.stages) if job.stages else {}
        current_stages[failed_stage] = "failed"
        # Cancel remaining pending stages
        for s, state in current_stages.items():
            if state == "pending":
                current_stages[s] = "cancelled"
        job.stages        = current_stages
        job.status        = "failed"
        job.current_stage = None
        db.commit()


# ── Worker Crew ────────────────────────────────────────────────────────────────

crew = [
    Harvester("Python-Harvester-1", "Python"),
    Harvester("Python-Harvester-2", "Python"),
    Harvester("JS-Harvester",       "JavaScript"),
    Harvester("CPP-Harvester",      "C++"),
    Harvester("General-Laborer",    "Generic"),
]


# ── Reaper Thread ──────────────────────────────────────────────────────────────

def reaper_loop():
    """
    Scans for jobs stuck in 'running' state whose worker hasn't sent a
    heartbeat within ORPHAN_THRESHOLD seconds, then re-enqueues them.
    """
    print("[REAPER] 👁️  Reaper thread started.")
    while True:
        time.sleep(REAPER_INTERVAL)
        db = SessionLocal()
        try:
            threshold = datetime.datetime.utcnow() - datetime.timedelta(
                seconds=ORPHAN_THRESHOLD
            )
            orphans = (
                db.query(Job)
                .filter(
                    Job.status == "running",
                    Job.last_heartbeat < threshold,
                )
                .all()
            )
            for job in orphans:
                print(
                    f"[REAPER] ♻️  Orphaned job {job.id[:8]} "
                    f"(last heartbeat: {job.last_heartbeat}) — re-enqueuing."
                )
                job.status        = "queued"
                job.worker_id     = None
                job.current_stage = None
                db.commit()
                r.zadd("job_priority_queue", {job.id: job.priority})

                # Free up any worker that was holding this job
                for worker in crew:
                    if worker.busy:   # best-effort; worker.busy is eventually consistent
                        pass          # worker will self-clear when its thread ends
        except Exception as exc:
            print(f"[REAPER] ⚠️  Error: {exc}")
        finally:
            db.close()


# ── Manager Loop ───────────────────────────────────────────────────────────────

def run_manager():
    print("\n" + "=" * 55)
    print("🌾 HALF CLUTCH WORKER MANAGER STARTING")
    print("   Pausing 5 s — run triple_harvester.py now to fill queue!")
    print("=" * 55 + "\n")

    # Start the Reaper in the background
    threading.Thread(target=reaper_loop, daemon=True).start()

    time.sleep(5)
    print("🚜 Harvesters entering the fields!\n")

    while True:
        # ZPOPMAX → highest priority job first
        job_data = r.zpopmax("job_priority_queue")

        if job_data:
            job_id, priority = job_data[0]
            clean_id = job_id.decode("utf-8") if isinstance(job_id, bytes) else job_id

            db = SessionLocal()
            try:
                job = db.query(Job).filter(Job.id == clean_id).first()
                if not job:
                    db.close()
                    continue

                assigned = False

                # 1. Try specialist first
                for worker in crew:
                    if not worker.busy and worker.specialty == job.language:
                        threading.Thread(
                            target=worker.process_job,
                            args=(job_id, priority),
                            daemon=True,
                        ).start()
                        assigned = True
                        break

                # 2. Fallback to General-Laborer
                if not assigned:
                    for worker in crew:
                        if not worker.busy and worker.specialty == "Generic":
                            threading.Thread(
                                target=worker.process_job,
                                args=(job_id, priority),
                                daemon=True,
                            ).start()
                            assigned = True
                            break

                # 3. All workers busy → put back in queue
                if not assigned:
                    r.zadd("job_priority_queue", {clean_id: priority})

            finally:
                db.close()

        time.sleep(0.5)


if __name__ == "__main__":
    run_manager()
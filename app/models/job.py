from sqlalchemy import Column, String, JSON, Integer, DateTime
from app.db import Base
import datetime


class Job(Base):
    __tablename__ = "jobs"

    # Identity
    id = Column(String, primary_key=True, index=True)
    repo = Column(String)
    branch = Column(String)
    commit_sha = Column(String)

    # Worker routing
    language = Column(String)
    priority = Column(Integer, default=1)       # 1=Low, 2=Mid, 3=High
    worker_id = Column(String, nullable=True)

    # Status & Progress
    status = Column(String)                     # queued | running | completed | failed
    current_stage = Column(String, nullable=True)
    stages = Column(JSON, nullable=True)        # {"Fetch": "pending"|"running"|"completed"|"failed"}

    # Reliability: used by the Reaper to detect crashed workers
    last_heartbeat = Column(DateTime, nullable=True)
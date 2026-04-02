from sqlalchemy import Column, String, JSON, Integer #
from app.db import Base

class Job(Base):
    __tablename__ = "jobs"

    # Identity & Versioning
    id = Column(String, primary_key=True, index=True)
    repo = Column(String)
    branch = Column(String)
    commit_sha = Column(String) # Keep this!
    
    # New Harvest Logic
    language = Column(String)  # For assigning to specific workers (e.g., Python Picker)
    priority = Column(Integer, default=1)  # For your Priority Scheduling (1=Low, 3=High)
    worker_id = Column(String, nullable=True)  # To track which worker is currently ginning this job
    
    # Status & Progress
    status = Column(String)
    current_stage = Column(String, nullable=True)
    stages = Column(JSON, nullable=True)
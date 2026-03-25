from sqlalchemy import Column, String, JSON # type: ignore
from app.db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    repo = Column(String)
    branch = Column(String)
    commit_sha = Column(String)
    status = Column(String)
    
    current_stage = Column(String, nullable = True)
    stages = Column(JSON, nullable = True)
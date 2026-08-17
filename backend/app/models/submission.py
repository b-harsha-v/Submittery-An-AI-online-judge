import uuid
import enum
from sqlalchemy import Column, String, DateTime, Enum, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class SubmissionStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AC = "accepted"
    WA = "wrong_answer"
    TLE = "time_limit_exceeded"
    MLE = "memory_limit_exceeded"
    RE = "runtime_error"
    CE = "compilation_error"
    INTERNAL_ERROR = "internal_error"

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id = Column(UUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String, default="python", nullable=False)
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.QUEUED, nullable=False)
    
    runtime = Column(Float, nullable=True) # in seconds
    memory = Column(Integer, nullable=True) # in KB (kilobytes)
    error_message = Column(Text, nullable=True) # compile error or runtime exception trace
    results = Column(JSON, nullable=True) # Per-testcase results list
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User")
    problem = relationship("Problem", back_populates="submissions")

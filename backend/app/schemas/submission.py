from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from ..models.submission import SubmissionStatus

class SubmissionBase(BaseModel):
    code: str
    language: str = "python"

class SubmissionCreate(SubmissionBase):
    custom_input: Optional[str] = None

class SubmissionResponse(SubmissionBase):
    id: UUID
    user_id: UUID
    problem_id: UUID
    status: SubmissionStatus
    runtime: Optional[float] = None
    memory: Optional[int] = None
    error_message: Optional[str] = None
    results: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True

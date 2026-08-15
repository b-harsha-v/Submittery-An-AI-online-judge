from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .user import UserResponse

class CommentBase(BaseModel):
    content: str
    parent_id: Optional[UUID] = None

class CommentCreate(CommentBase):
    pass

class CommentResponse(BaseModel):
    id: UUID
    problem_id: UUID
    content: str
    parent_id: Optional[UUID] = None
    created_at: datetime
    user: UserResponse
    replies: List['CommentResponse'] = []

    class Config:
        from_attributes = True

CommentResponse.model_rebuild()

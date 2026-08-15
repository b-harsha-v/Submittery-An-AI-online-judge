from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.problem import ProblemDifficulty

class TestCaseBase(BaseModel):
    input: str
    expected_output: str
    is_sample: bool = False

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseResponse(TestCaseBase):
    id: UUID

    class Config:
        from_attributes = True

class ProblemBase(BaseModel):
    title: str
    description: str
    difficulty: ProblemDifficulty = ProblemDifficulty.EASY
    time_limit: float = 1.0
    memory_limit: int = 256
    tags: Optional[List[str]] = []
    starter_code: Optional[Dict[str, str]] = {}
    is_public: bool = True

class ProblemCreate(ProblemBase):
    test_cases: List[TestCaseCreate]

class ProblemResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str
    difficulty: ProblemDifficulty
    time_limit: float
    memory_limit: int
    tags: Optional[List[str]] = []
    starter_code: Optional[Dict[str, str]] = {}
    is_public: bool
    created_at: datetime
    test_cases: List[TestCaseResponse] # Typically only public/sample test cases are returned unless admin

    class Config:
        from_attributes = True

class ProblemListResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    difficulty: ProblemDifficulty
    tags: Optional[List[str]] = []
    is_public: bool

    class Config:
        from_attributes = True

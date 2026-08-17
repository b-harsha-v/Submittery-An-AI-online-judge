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

class ProblemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[ProblemDifficulty] = None
    time_limit: Optional[float] = None
    memory_limit: Optional[int] = None
    tags: Optional[List[str]] = None
    starter_code: Optional[Dict[str, str]] = None
    is_public: Optional[bool] = None
    test_cases: Optional[List[TestCaseCreate]] = None

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
    time_limit: Optional[float] = 1.0
    memory_limit: Optional[int] = 256
    tags: Optional[List[str]] = []
    is_public: bool

    class Config:
        from_attributes = True

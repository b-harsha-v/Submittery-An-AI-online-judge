from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
from ..database import get_db
from ..models.problem import Problem
from ..models.submission import Submission
from ..models.user import User
from ..services.ai_service import ai_service
from .deps import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])

class ComplexityRequest(BaseModel):
    code: str
    problem_id: UUID

class QARequest(BaseModel):
    question: str
    problem_id: UUID

class AIResponse(BaseModel):
    response: str

class ProblemRecommendResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    difficulty: str
    tags: Optional[List[str]] = []

    class Config:
        from_attributes = True

@router.post("/analyze-complexity", response_model=AIResponse)
def analyze_complexity(
    req: ComplexityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    problem = db.query(Problem).filter(Problem.id == req.problem_id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
        
    analysis = ai_service.analyze_complexity(req.code, problem.title)
    return {"response": analysis}

@router.post("/code-review/{submission_id}", response_model=AIResponse)
def code_review(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
        
    # Check authorization
    if submission.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this submission"
        )
        
    problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
    review = ai_service.provide_code_review(submission.code, problem.title, submission.status.value)
    return {"response": review}

@router.post("/debug-hints/{submission_id}", response_model=AIResponse)
def debug_hints(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
        
    # Check authorization
    if submission.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this submission"
        )
        
    problem = db.query(Problem).filter(Problem.id == submission.problem_id).first()
    error_msg = submission.error_message or "Submission was not accepted."
    hints = ai_service.generate_debug_hints(submission.code, problem.title, error_msg)
    return {"response": hints}

@router.post("/ask", response_model=AIResponse)
def ask_question(
    req: QARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    problem = db.query(Problem).filter(Problem.id == req.problem_id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
        
    answer = ai_service.answer_question(req.question, problem)
    return {"response": answer}

@router.get("/recommend/{problem_id}", response_model=List[ProblemRecommendResponse])
def recommend_problems(
    problem_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not current_problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
        
    all_problems = db.query(Problem).filter(Problem.is_public == True).all()
    recommendations = ai_service.recommend_problems(current_problem, all_problems)
    
    # Map model difficulty Enum if needed
    for rec in recommendations:
        if hasattr(rec.difficulty, "value"):
            rec.difficulty_str = rec.difficulty.value
        else:
            rec.difficulty_str = rec.difficulty
            
    return recommendations

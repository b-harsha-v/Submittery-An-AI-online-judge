from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..models.submission import Submission, SubmissionStatus
from ..models.problem import Problem
from ..models.user import User
from ..schemas.submission import SubmissionCreate, SubmissionResponse
from ..services.queue_service import queue_service
from .deps import get_current_user

import httpx
from ..config import settings
from ..models.problem import TestCase

router = APIRouter(prefix="/submissions", tags=["submissions"])

@router.post("/run/{problem_id}")
def run_code(
    problem_id: UUID,
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify problem exists
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
        
    # Get ONLY sample test cases
    test_cases = db.query(TestCase).filter(
        TestCase.problem_id == problem.id,
        TestCase.is_sample == True
    ).all()
    
    if not test_cases:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No sample test cases available for this problem."
        )
        
    # Prepare payload for compiler service
    payload = {
        "code": submission_in.code,
        "language": submission_in.language,
        "time_limit": problem.time_limit,
        "memory_limit": problem.memory_limit,
        "test_cases": [
            {
                "id": str(tc.id),
                "input": tc.input,
                "expected_output": tc.expected_output
            }
            for tc in test_cases
        ]
    }
    
    # Call Compiler Service directly
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{settings.COMPILER_SERVICE_URL}/execute",
                json=payload,
                timeout=float(problem.time_limit * len(test_cases)) + 5.0
            )
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Compiler Service error: {response.text}"
            )
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute code: {str(e)}"
        )


@router.post("/submit/{problem_id}", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_code(
    problem_id: UUID,
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify problem exists
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
        
    # Create submission in database
    submission = Submission(
        user_id=current_user.id,
        problem_id=problem.id,
        code=submission_in.code,
        language=submission_in.language,
        status=SubmissionStatus.QUEUED
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    # Enqueue in Redis
    try:
        queue_service.push_submission(str(submission.id))
        # Publish initial QUEUED state
        queue_service.publish_status_update(
            submission_id=str(submission.id),
            status=SubmissionStatus.QUEUED.value
        )
    except Exception as e:
        # If queueing fails, mark submission as INTERNAL_ERROR
        submission.status = SubmissionStatus.INTERNAL_ERROR
        submission.error_message = f"Failed to enqueue job: {str(e)}"
        db.commit()
        db.refresh(submission)
        
    return submission

@router.get("/{id}", response_model=SubmissionResponse)
def get_submission(
    id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    submission = db.query(Submission).filter(Submission.id == id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
        
    # Standard users can only view their own submissions
    if submission.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission"
        )
        
    return submission

@router.get("/problem/{problem_id}", response_model=List[SubmissionResponse])
def get_problem_submissions(
    problem_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    submissions = db.query(Submission).filter(
        Submission.problem_id == problem_id,
        Submission.user_id == current_user.id
    ).order_by(Submission.created_at.desc()).all()
    return submissions

@router.get("/", response_model=List[SubmissionResponse])
def get_all_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    return db.query(Submission).order_by(Submission.created_at.desc()).limit(50).all()


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..models.problem import Problem, TestCase, ProblemDifficulty
from ..models.user import User, UserRole
from ..schemas.problem import ProblemCreate, ProblemUpdate, ProblemResponse, ProblemListResponse
from .deps import get_current_user, get_current_admin

router = APIRouter(prefix="/problems", tags=["problems"])

@router.get("/", response_model=List[ProblemListResponse])
def list_problems(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Admins see all problems, regular users only public ones
    if current_user.role == UserRole.ADMIN:
        problems = db.query(Problem).all()
    else:
        problems = db.query(Problem).filter(Problem.is_public == True).all()
    return problems

@router.get("/{slug}", response_model=ProblemResponse)
def get_problem(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    problem = db.query(Problem).filter(Problem.slug == slug).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
        
    if not problem.is_public and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Problem is not public"
        )
        
    # We want to filter test cases so that standard users ONLY receive the public/sample ones.
    # We can do this dynamically since SQLAlchemy models can be read, but let's make sure
    # the response schema serialization filters it.
    # To be explicit, we return a copy with only sample test cases for normal users.
    sample_cases = [tc for tc in problem.test_cases if tc.is_sample]
    
    # If admin, return all cases, otherwise return sample cases
    test_cases_to_return = problem.test_cases if current_user.role == UserRole.ADMIN else sample_cases
    
    # Construct response
    return {
        "id": problem.id,
        "title": problem.title,
        "slug": problem.slug,
        "description": problem.description,
        "difficulty": problem.difficulty,
        "time_limit": problem.time_limit,
        "memory_limit": problem.memory_limit,
        "tags": problem.tags,
        "starter_code": problem.starter_code,
        "is_public": problem.is_public,
        "created_at": problem.created_at,
        "test_cases": test_cases_to_return
    }

@router.post("/", response_model=ProblemResponse, status_code=status.HTTP_201_CREATED)
def create_problem(
    problem_in: ProblemCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Check if slug exists
    slug = problem_in.title.lower().replace(" ", "-").replace("_", "-")
    # Clean slug
    import re
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    
    if db.query(Problem).filter(Problem.slug == slug).first():
        # append a random suffix to make it unique
        import uuid
        slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        
    problem = Problem(
        title=problem_in.title,
        slug=slug,
        description=problem_in.description,
        difficulty=problem_in.difficulty,
        time_limit=problem_in.time_limit,
        memory_limit=problem_in.memory_limit,
        tags=problem_in.tags,
        starter_code=problem_in.starter_code,
        is_public=problem_in.is_public
    )
    db.add(problem)
    db.flush() # Populate problem.id
    
    # Create test cases
    for tc_in in problem_in.test_cases:
        tc = TestCase(
            problem_id=problem.id,
            input=tc_in.input,
            expected_output=tc_in.expected_output,
            is_sample=tc_in.is_sample
        )
        db.add(tc)
        
    db.commit()
    db.refresh(problem)
    return problem

@router.put("/{id}", response_model=ProblemResponse)
def update_problem(
    id: UUID,
    problem_in: ProblemUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    problem = db.query(Problem).filter(Problem.id == id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    
    if problem_in.title is not None:
        problem.title = problem_in.title
    if problem_in.description is not None:
        problem.description = problem_in.description
    if problem_in.difficulty is not None:
        problem.difficulty = problem_in.difficulty
    if problem_in.time_limit is not None:
        problem.time_limit = problem_in.time_limit
    if problem_in.memory_limit is not None:
        problem.memory_limit = problem_in.memory_limit
    if problem_in.tags is not None:
        problem.tags = problem_in.tags
    if problem_in.starter_code is not None:
        problem.starter_code = problem_in.starter_code
    if problem_in.is_public is not None:
        problem.is_public = problem_in.is_public
        
    # If test cases are provided, replace existing test cases
    if problem_in.test_cases is not None:
        db.query(TestCase).filter(TestCase.problem_id == problem.id).delete()
        for tc_in in problem_in.test_cases:
            tc = TestCase(
                problem_id=problem.id,
                input=tc_in.input,
                expected_output=tc_in.expected_output,
                is_sample=tc_in.is_sample
            )
            db.add(tc)
            
    db.commit()
    db.refresh(problem)
    return problem

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(
    id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    problem = db.query(Problem).filter(Problem.id == id).first()
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found"
        )
    db.delete(problem)
    db.commit()
    return None

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from ..database import get_db
from ..models.discussion import Comment
from ..models.problem import Problem
from ..models.user import User
from ..schemas.discussion import CommentCreate, CommentResponse
from .deps import get_current_user

router = APIRouter(prefix="/discussion", tags=["discussion"])

@router.get("/problem/{problem_id}", response_model=List[CommentResponse])
def get_problem_discussions(
    problem_id: UUID,
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
        
    # Get top-level comments (where parent_id is Null)
    comments = db.query(Comment).filter(
        Comment.problem_id == problem_id,
        Comment.parent_id == None
    ).order_by(Comment.created_at.desc()).all()
    
    return comments

@router.post("/problem/{problem_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def post_comment(
    problem_id: UUID,
    comment_in: CommentCreate,
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
        
    # If parent_id is specified, verify the parent comment exists
    if comment_in.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment_in.parent_id).first()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )
            
    comment = Comment(
        problem_id=problem_id,
        user_id=current_user.id,
        content=comment_in.content,
        parent_id=comment_in.parent_id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment

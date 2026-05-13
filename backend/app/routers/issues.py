from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import Issue, get_db
from app.schemas.issue import (
    IssueBoard,
    IssueCreate,
    IssueMove,
    IssueOut,
    IssueStatus,
    IssueUpdate,
)
from app.services import issue_service

router = APIRouter(prefix="/issues", tags=["issues"])


def _get(db: Session, issue_id: int) -> Issue:
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if issue is None:
        raise HTTPException(status_code=404, detail="issue not found")
    return issue


@router.get("", response_model=IssueBoard)
def get_board(db: Session = Depends(get_db)):
    return issue_service.list_board(db)


@router.get("/list", response_model=List[IssueOut])
def list_issues(
    status: Optional[IssueStatus] = Query(None),
    db: Session = Depends(get_db),
):
    return issue_service.list_flat(db, status)


@router.get("/{issue_id}", response_model=IssueOut)
def get_one(issue_id: int, db: Session = Depends(get_db)):
    issue = _get(db, issue_id)
    counts = issue_service.message_count_map(db, [issue.id])
    return {
        "id": issue.id,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status,
        "position": issue.position,
        "message_count": counts.get(issue.id, 0),
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
        "completed_at": issue.completed_at,
    }


@router.post("", response_model=IssueOut, status_code=201)
def create(payload: IssueCreate, db: Session = Depends(get_db)):
    issue = issue_service.create_issue(db, payload.title, payload.description, payload.status)
    db.commit()
    db.refresh(issue)
    return {
        "id": issue.id,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status,
        "position": issue.position,
        "message_count": 0,
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
        "completed_at": issue.completed_at,
    }


@router.patch("/{issue_id}", response_model=IssueOut)
def update(issue_id: int, payload: IssueUpdate, db: Session = Depends(get_db)):
    issue = _get(db, issue_id)
    issue_service.update_issue(db, issue, payload.title, payload.description)
    db.commit()
    db.refresh(issue)
    counts = issue_service.message_count_map(db, [issue.id])
    return {
        "id": issue.id,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status,
        "position": issue.position,
        "message_count": counts.get(issue.id, 0),
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
        "completed_at": issue.completed_at,
    }


@router.patch("/{issue_id}/move", response_model=IssueOut)
def move(issue_id: int, payload: IssueMove, db: Session = Depends(get_db)):
    issue = _get(db, issue_id)
    issue_service.move_issue(db, issue, payload.status, payload.position)
    db.commit()
    db.refresh(issue)
    counts = issue_service.message_count_map(db, [issue.id])
    return {
        "id": issue.id,
        "title": issue.title,
        "description": issue.description,
        "status": issue.status,
        "position": issue.position,
        "message_count": counts.get(issue.id, 0),
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
        "completed_at": issue.completed_at,
    }


@router.delete("/{issue_id}", status_code=204)
def delete(issue_id: int, db: Session = Depends(get_db)):
    issue = _get(db, issue_id)
    issue_service.delete_issue(db, issue)
    db.commit()

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.issue.schemas import (
    IssueBoard,
    IssueCreate,
    IssueMove,
    IssueOut,
    IssueStatus,
    IssueUpdate,
)
from app.modules.issue import service as issue_service

router = APIRouter(prefix="/issues", tags=["issues"])


def _get(db: Session, issue_id: int):
    try: return issue_service.get(db, issue_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


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
    issue = issue_service.create_use_case(db, payload.title, payload.description, payload.status)
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
    try: issue = issue_service.update_use_case(db, issue_id, payload.title, payload.description)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
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
    try: issue = issue_service.move_use_case(db, issue_id, payload.status, payload.position)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
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
    try: issue_service.delete_use_case(db, issue_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

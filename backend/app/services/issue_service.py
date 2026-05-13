"""Issue 看板列内/跨列移动的位置重排逻辑(四列版,仿 todo_service)。"""
from datetime import datetime
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Issue, Message
from app.schemas.issue import IssueStatus

DONE_LIMIT = 20
ALL_STATUSES: List[IssueStatus] = ["doing", "done", "archived", "abandoned"]


def _column(db: Session, status: IssueStatus) -> List[Issue]:
    return (
        db.query(Issue).filter(Issue.status == status).order_by(Issue.position.asc()).all()
    )


def _renumber(issues: List[Issue]) -> None:
    for i, t in enumerate(issues):
        if t.position != i:
            t.position = i


def message_count_map(db: Session, issue_ids: List[int]) -> Dict[int, int]:
    if not issue_ids:
        return {}
    rows = (
        db.query(Message.issue_id, func.count(Message.id))
        .filter(Message.issue_id.in_(issue_ids))
        .group_by(Message.issue_id)
        .all()
    )
    return {row[0]: row[1] for row in rows}


def attach_message_count(db: Session, issues: List[Issue]) -> List[dict]:
    counts = message_count_map(db, [i.id for i in issues])
    result = []
    for it in issues:
        result.append({
            "id": it.id,
            "title": it.title,
            "description": it.description,
            "status": it.status,
            "position": it.position,
            "message_count": counts.get(it.id, 0),
            "created_at": it.created_at,
            "updated_at": it.updated_at,
            "completed_at": it.completed_at,
        })
    return result


def list_board(db: Session) -> dict:
    doing = _column(db, "doing")
    done = (
        db.query(Issue)
        .filter(Issue.status == "done")
        .order_by(Issue.completed_at.desc().nullslast(), Issue.id.desc())
        .limit(DONE_LIMIT)
        .all()
    )
    archived = (
        db.query(Issue)
        .filter(Issue.status == "archived")
        .order_by(Issue.updated_at.desc(), Issue.id.desc())
        .limit(DONE_LIMIT)
        .all()
    )
    abandoned = (
        db.query(Issue)
        .filter(Issue.status == "abandoned")
        .order_by(Issue.updated_at.desc(), Issue.id.desc())
        .limit(DONE_LIMIT)
        .all()
    )
    return {
        "doing": attach_message_count(db, doing),
        "done": attach_message_count(db, done),
        "archived": attach_message_count(db, archived),
        "abandoned": attach_message_count(db, abandoned),
    }


def list_flat(db: Session, status: IssueStatus | None = None) -> List[dict]:
    q = db.query(Issue)
    if status:
        q = q.filter(Issue.status == status)
    issues = q.order_by(Issue.status, Issue.position.asc()).all()
    return attach_message_count(db, issues)


def create_issue(db: Session, title: str, description: str | None, status: IssueStatus = "doing") -> Issue:
    col = _column(db, status)
    issue = Issue(title=title, description=description, status=status, position=len(col))
    if status == "done":
        issue.completed_at = datetime.now()
    db.add(issue)
    db.flush()
    return issue


def move_issue(db: Session, issue: Issue, target_status: IssueStatus, target_pos: int) -> None:
    src_status = issue.status
    target_col = [t for t in _column(db, target_status) if t.id != issue.id]
    insert_at = max(0, min(target_pos, len(target_col)))

    if target_status == "done" and src_status != "done":
        issue.completed_at = datetime.now()
    elif target_status != "done" and src_status == "done":
        issue.completed_at = None
    issue.status = target_status

    target_col.insert(insert_at, issue)
    _renumber(target_col)

    if src_status != target_status:
        src_col = [t for t in _column(db, src_status) if t.id != issue.id]
        _renumber(src_col)


def update_issue(db: Session, issue: Issue, title: str | None, description: str | None) -> None:
    if title is not None:
        issue.title = title
    if description is not None:
        issue.description = description


def delete_issue(db: Session, issue: Issue) -> None:
    status = issue.status
    db.delete(issue)
    db.flush()
    col = _column(db, status)
    _renumber(col)

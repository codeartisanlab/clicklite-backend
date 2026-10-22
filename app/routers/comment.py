from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.comment import Comment
from app.models.task import Task
from app.models.user import User
from app.routers.task import get_owned_project
from app.schemas.comment import CommentCreate, CommentResponse
from app.routers.notification import add_notification


def get_owned_task(
    db: Session,
    project_id: str,
    task_id: str,
    current_user: User,
) -> Task:
    project = get_owned_project(db, project_id, current_user)

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.project_id == project.id,
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


def to_comment_response(comment: Comment, author_name: str) -> CommentResponse:
    return CommentResponse(
        id=str(comment.id),
        body=comment.body,
        task_id=str(comment.task_id),
        author_name=author_name,
        created_at=comment.created_at,
    )


router = APIRouter(
    prefix="/api/projects/{project_id}/tasks/{task_id}/comments",
    tags=["Comments"],
)


@router.get(
    "",
    response_model=list[CommentResponse],
)
def get_comments(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_owned_task(db, project_id, task_id, current_user)

    rows = (
        db.query(Comment, User)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.task_id == task.id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    return [
        to_comment_response(comment, user.full_name)
        for comment, user in rows
    ]


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    project_id: str,
    task_id: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_owned_task(db, project_id, task_id, current_user)

    comment = Comment(
        body=data.body.strip(),
        task_id=task.id,
        user_id=current_user.id,
    )

    db.add(comment)

    add_notification(
        db,
        user_id=current_user.id,
        kind="comment",
        message=f"New comment on {task.title}",
        link=f"/projects/{project_id}/tasks/{task.id}",
    )

    db.commit()
    db.refresh(comment)

    return to_comment_response(comment, current_user.full_name)
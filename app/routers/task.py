from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate,TaskCalendarResponse
from app.models.comment import Comment

def get_owned_project(
    db: Session,
    project_id: str,
    current_user: User,
) -> Project:
    project = (
        db.query(Project)
        .join(
            Workspace,
            Project.workspace_id == Workspace.id,
        )
        .filter(
            Project.id == project_id,
            Workspace.owner_id == current_user.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


def to_task_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=str(task.id),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assignee=task.assignee,
        due_date=task.due_date,
        project_id=str(task.project_id),
        updated_at=task.updated_at,
    )


router = APIRouter(
    prefix="/api/projects/{project_id}/tasks",
    tags=["Tasks"],
)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: str,
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(db, project_id, current_user)

    task = Task(
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        assignee=data.assignee,
        due_date=data.due_date,
        project_id=project.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return to_task_response(task)


@router.get(
    "",
    response_model=list[TaskResponse],
)
def get_tasks(
    project_id: str,
    due: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_owned_project(db, project_id, current_user)

    tasks_query = db.query(Task).filter(Task.project_id == project.id)

    if due:
        tasks_query = tasks_query.filter(
            Task.due_date.is_not(None),
            Task.due_date <= date.today(),
            Task.status != "done",
        ).order_by(Task.due_date.asc())
    else:
        tasks_query = tasks_query.order_by(Task.created_at.desc())

    return [to_task_response(task) for task in tasks_query.all()]


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    return to_task_response(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    project_id: str,
    task_id: str,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    updates = data.model_dump(exclude_unset=True)

    if "title" in updates:
        task.description = updates["title"].strip()

    if "description" in updates:
        task.description = updates["description"]

    if "status" in updates:
        task.status = updates["status"]

    if "priority" in updates:
        task.priority = updates["priority"]

    if "assignee" in updates:
        task.assignee = updates["assignee"]

    if "due_date" in updates:
        task.due_date = updates["due_date"]

    db.commit()
    db.refresh(task)

    return to_task_response(task)


calendar_router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
)


@calendar_router.get(
    "",
    response_model=list[TaskCalendarResponse],
)
def get_calendar_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Task, Project)
        .join(Project, Task.project_id == Project.id)
        .join(Workspace, Project.workspace_id == Workspace.id)
        .filter(
            Workspace.owner_id == current_user.id,
            Task.due_date.is_not(None),
        )
        .order_by(Task.due_date.asc())
        .all()
    )

    return [
        TaskCalendarResponse(
            id=str(task.id),
            title=task.title,
            due_date=task.due_date,
            status=task.status,
            project_id=str(project.id),
            project_name=project.name,
        )
        for task, project in rows
    ]


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    project_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    comments = (
        db.query(Comment)
        .filter(Comment.task_id == task.id)
        .all()
    )

    for comment in comments:
        db.delete(comment)

    db.delete(task)
    db.commit()
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.task import TaskCreate, TaskResponse


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

    task = Task(
        title=data.title,
        description=data.description,
        status=data.status,
        project_id=project.id,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return TaskResponse(
        id=str(task.id),
        title=task.title,
        description=task.description,
        status=task.status,
        project_id=str(task.project_id),
    )
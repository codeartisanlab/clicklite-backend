from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.search import SearchProject, SearchResponse, SearchTask

router = APIRouter(
    prefix="/api/search",
    tags=["Search"],
)


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    term = f"%{q.strip()}%"

    project_rows = (
        db.query(Project, Workspace)
        .join(Workspace, Project.workspace_id == Workspace.id)
        .filter(
            Workspace.owner_id == current_user.id,
            Project.name.ilike(term),
        )
        .order_by(Project.name)
        .limit(8)
        .all()
    )

    task_rows = (
        db.query(Task, Project)
        .join(Project, Task.project_id == Project.id)
        .join(Workspace, Project.workspace_id == Workspace.id)
        .filter(
            Workspace.owner_id == current_user.id,
            Task.title.ilike(term),
        )
        .order_by(Task.title)
        .limit(8)
        .all()
    )

    return SearchResponse(
        projects=[
            SearchProject(
                id=str(project.id),
                name=project.name,
                workspace_name=workspace.name,
            )
            for project, workspace in project_rows
        ],
        tasks=[
            SearchTask(
                id=str(task.id),
                title=task.title,
                project_id=str(project.id),
                project_name=project.name,
            )
            for task, project in task_rows
        ],
    )
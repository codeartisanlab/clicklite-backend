from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse


router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
)

# create new project
@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = (
        db.query(Workspace)
        .filter(
            Workspace.id == data.workspace_id,
            Workspace.owner_id == current_user.id,
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    project = Project(
        name=data.name,
        description=data.description,
        workspace_id=workspace.id,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        workspace_id=str(project.workspace_id),
    )

# Project list according to workspace
@router.get(
    "/{workspace_id}",
    response_model=list[ProjectResponse],
)
def get_projects(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = (
        db.query(Workspace)
        .filter(
            Workspace.id == workspace_id,
            Workspace.owner_id == current_user.id,
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    projects = (
        db.query(Project)
        .filter(Project.workspace_id == workspace.id)
        .all()
    )

    return [
        ProjectResponse(
            id=str(project.id),
            name=project.name,
            description=project.description,
            workspace_id=str(project.workspace_id),
        )
        for project in projects
    ]

# Project detail
@router.get(
    "/detail/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: str,
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

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        workspace_id=str(project.workspace_id),
    )

# All project list
@router.get(
    "",
    response_model=list[ProjectResponse],
)
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(Project, Workspace)
        .join(
            Workspace,
            Project.workspace_id == Workspace.id,
        )
        .filter(
            Workspace.owner_id == current_user.id,
        )
        .all()
    )

    return [
        ProjectResponse(
            id=str(project.id),
        name=project.name,
        description=project.description,
        workspace_id=str(workspace.id),
        workspace_name=workspace.name
        )
        for project, workspace in projects
    ]
from fastapi import APIRouter, Depends, status,HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
)

router = APIRouter(
    prefix="/api/workspaces",
    tags=["Workspaces"],
)

@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = Workspace(
        name=data.name,
        color=data.color,
        owner_id=current_user.id,
    )

    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        color=workspace.color,
        owner_id=str(workspace.owner_id),
    )


@router.get(
    "",
    response_model=list[WorkspaceResponse],
)
def get_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspaces = (
        db.query(Workspace)
        .filter(Workspace.owner_id == current_user.id)
        .all()
    )

    return [
        WorkspaceResponse(
            id=str(workspace.id),
            name=workspace.name,
            color=workspace.color,
            owner_id=str(workspace.owner_id),
        )
        for workspace in workspaces
    ]

@router.get(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
def get_workspace(
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

    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        color=workspace.color,
        owner_id=str(workspace.owner_id),
    )
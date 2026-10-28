from fastapi import APIRouter, Depends, status,HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.member import Member
from app.models.project import Project
from app.models.task import Task
from app.models.comment import Comment
from app.models.activity import Activity
from app.models.workspace import Workspace
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate
)

# Acess workspace by member
def can_access_workspace(db, workspace_id, user):
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .first()
    )

    if workspace is None:
        return None

    if workspace.owner_id == user.id:
        return workspace

    member = (
        db.query(Member)
        .filter(
            Member.workspace_id == workspace.id,
            Member.user_id == user.id,
        )
        .first()
    )

    if member is None:
        return None

    return workspace

# Routes
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
    owned = (
        db.query(Workspace)
        .filter(Workspace.owner_id == current_user.id)
        .all()
    )
    joined = (
        db.query(Workspace)
        .join(Member, Member.workspace_id == Workspace.id)
        .filter(Member.user_id == current_user.id)
        .all()
    )
    seen = {workspace.id for workspace in owned}
    workspaces = owned + [
        workspace for workspace in joined
        if workspace.id not in seen
    ]

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
    
    workspace = can_access_workspace(db, workspace_id, current_user)

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
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

@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceResponse,
)
def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
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

    updates = data.model_dump(exclude_unset=True)

    if updates.get("name"):
        workspace.name = updates["name"].strip()

    if updates.get("color"):
        workspace.color = updates["color"]

    db.commit()
    db.refresh(workspace)

    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        color=workspace.color,
        owner_id=str(workspace.owner_id),
    )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_workspace(
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

    projects = db.query(Project).filter(Project.workspace_id == workspace.id).all()

    for project in projects:
        tasks = db.query(Task).filter(Task.project_id == project.id).all()

        for task in tasks:
            comments = db.query(Comment).filter(Comment.task_id == task.id).all()

            for comment in comments:
                db.delete(comment)

            db.delete(task)

        db.delete(project)

    
    activities = db.query(Activity).filter(Activity.workspace_id == workspace.id).all()
    for activity in activities:
        db.delete(activity)

    db.delete(workspace)
    db.commit()
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.activity import Activity
from app.models.user import User
from app.routers.workspace import can_access_workspace
from app.schemas.activity import ActivityResponse


def add_activity(
    db: Session,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    kind: str,
    message: str,
    link: str,
) -> None:
    db.add(
        Activity(
            workspace_id=workspace_id,
            user_id=user_id,
            kind=kind,
            message=message,
            link=link,
        )
    )


router = APIRouter(
    prefix="/api/workspaces",
    tags=["Activity"],
)


@router.get(
    "/{workspace_id}/activity",
    response_model=list[ActivityResponse],
)
def get_activity(
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

    rows = (
        db.query(Activity, User)
        .join(User, Activity.user_id == User.id)
        .filter(Activity.workspace_id == workspace.id)
        .order_by(Activity.created_at.desc())
        .limit(10)
        .all()
    )

    return [
        ActivityResponse(
            id=str(activity.id),
            user_name=user.full_name,
            message=activity.message,
            link=activity.link,
            created_at=activity.created_at,
        )
        for activity, user in rows
    ]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User

from app.models.member import Member
from app.models.workspace import Workspace
from app.schemas.member import MemberCreate, MemberResponse

router = APIRouter(
    prefix="/api/workspaces",
    tags=["Workspaces"],
)

@router.get(
    "/{workspace_id}/members",
    response_model=list[MemberResponse],
)
def get_members(
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

    owner = db.query(User).filter(User.id == workspace.owner_id).first()
    members = [
        MemberResponse(
            id=str(owner.id),
            full_name=owner.full_name,
            email=owner.email,
            role="owner",
        )
    ]

    rows = (
        db.query(Member, User)
        .join(User, Member.user_id == User.id)
        .filter(Member.workspace_id == workspace.id)
        .all()
    )

    for member, user in rows:
        members.append(
            MemberResponse(
                id=str(member.id),
                full_name=user.full_name,
                email=user.email,
                role=member.role,
            )
        )

    return members


@router.post(
    "/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_member(
    workspace_id: str,
    data: MemberCreate,
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

    invited_user = (
        db.query(User)
        .filter(User.email == data.email.strip().lower())
        .first()
    )

    if not invited_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account with that email",
        )

    if invited_user.id == workspace.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already the owner",
        )

    existing = (
        db.query(Member)
        .filter(
            Member.workspace_id == workspace.id,
            Member.user_id == invited_user.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member",
        )

    member = Member(
        workspace_id=workspace.id,
        user_id=invited_user.id,
        role=data.role.strip(),
    )

    db.add(member)
    db.commit()
    db.refresh(member)

    return MemberResponse(
        id=str(member.id),
        full_name=invited_user.full_name,
        email=invited_user.email,
        role=member.role,
    )
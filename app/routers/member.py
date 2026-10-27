from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User

from app.models.member import Member
from app.models.workspace_invites import WorkspaceInvite
from app.models.workspace import Workspace
from app.schemas.member import MemberCreate, MemberResponse,InviteAccept

from app.core.email import send_invite_email
from app.core.config import settings
from datetime import timedelta,datetime,timezone
from app.core.security import hash_reset_token,create_reset_token

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


# Send workspace Invitation
@router.post(
    "/{workspace_id}/members",
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

    email = data.email.strip().lower()

    if email == current_user.email.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user is already the owner",
        )

    invited_user = db.query(User).filter(User.email == email).first()

    if invited_user is not None:
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

    now = datetime.now(timezone.utc)
    old_invites = (
        db.query(WorkspaceInvite)
        .filter(
            WorkspaceInvite.workspace_id == workspace.id,
            WorkspaceInvite.email == email,
            WorkspaceInvite.used_at.is_(None),
        )
        .all()
    )

    for old_invite in old_invites:
        old_invite.used_at = now

    raw_token = create_reset_token()
    invite = WorkspaceInvite(
        workspace_id=workspace.id,
        email=email,
        role=data.role.strip(),
        token_hash=hash_reset_token(raw_token),
        expires_at=now + timedelta(days=7),
    )

    db.add(invite)
    db.commit()

    invite_url = f"{settings.FRONTEND_URL}/invite?token={raw_token}"
    send_invite_email(email, invite_url)

    return {"message": "Invitation sent"}


invite_router = APIRouter(
    prefix="/api/invites",
    tags=["Invites"],
)

# Accept the invitation
@invite_router.post("/accept")
def accept_invite(
    data: InviteAccept,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invite = (
        db.query(WorkspaceInvite)
        .filter(WorkspaceInvite.token_hash == hash_reset_token(data.token))
        .first()
    )

    now = datetime.now(timezone.utc)

    if (
        invite is None
        or invite.used_at is not None
        or invite.expires_at < now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation is invalid or expired",
        )

    if current_user.email.strip().lower() != invite.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Log in with the invited email",
        )

    existing = (
        db.query(Member)
        .filter(
            Member.workspace_id == invite.workspace_id,
            Member.user_id == current_user.id,
        )
        .first()
    )

    if existing is None:
        db.add(
            Member(
                workspace_id=invite.workspace_id,
                user_id=current_user.id,
                role=invite.role,
            )
        )

    invite.used_at = now
    db.commit()

    return {"message": "You joined the workspace"}
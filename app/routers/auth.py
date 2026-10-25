from fastapi import APIRouter, Depends, HTTPException, status,Cookie,Response
from sqlalchemy.orm import Session

from app.core.security import hash_password,verify_password,create_access_token,decode_access_token,hash_reset_token,create_reset_token
from app.db.database import get_db
from app.models.user import User
from app.models.password_reset import PasswordReset
from app.schemas.auth import RegisterRequest, UserResponse,TokenResponse,LoginRequest,ProfileUpdate,ForgotPasswordRequest,ResetPasswordRequest
from app.core.dependencies import get_current_user
from app.core.email import send_reset_email
from app.core.config import settings
from datetime import timedelta,datetime,timezone


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        bio=user.bio,
        theme=user.theme or "light",
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)

def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return to_user_response(user)



failed_tries: dict[str, list[datetime]] = {}

def too_many_tries(email: str) -> bool:
    now = datetime.now(timezone.utc)
    kept = []

    for tried_at in failed_tries.get(email, []):
        if now - tried_at < timedelta(minutes=15):
            kept.append(tried_at)

    failed_tries[email] = kept
    return len(kept) >= 5


def remember_failed_try(email: str) -> None:
    if email not in failed_tries:
        failed_tries[email] = []

    failed_tries[email].append(datetime.now(timezone.utc))


def forget_failed_tries(email: str) -> None:
    if email in failed_tries:
        del failed_tries[email]


# Login
@router.post(
    "/login"
)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    if too_many_tries(data.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in 15 minutes.",
        )

    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if not user:
        remember_failed_try(data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.password_hash):
        remember_failed_try(data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    forget_failed_tries(data.email)

    access_token = create_access_token(str(user.id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {
        "message": "Login successful"
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token"
    )

    return {
        "message": "Logout successful"
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return to_user_response(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    full_name = data.full_name.strip()

    if len(full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must be at least 2 characters",
        )

    current_user.full_name = full_name
    current_user.phone = data.phone.strip() if data.phone and data.phone.strip() else None
    current_user.bio = data.bio.strip() if data.bio and data.bio.strip() else None
    current_user.theme = data.theme

    db.commit()
    db.refresh(current_user)

    return to_user_response(current_user)


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if user:
        now = datetime.now(timezone.utc)

        old_resets = (
            db.query(PasswordReset)
            .filter(
                PasswordReset.user_id == user.id,
                PasswordReset.used_at.is_(None),
            )
            .all()
        )

        for old_reset in old_resets:
            old_reset.used_at = now

        raw_token = create_reset_token()

        reset = PasswordReset(
            user_id=user.id,
            token_hash=hash_reset_token(raw_token),
            expires_at=now + timedelta(minutes=30),
        )

        db.add(reset)
        db.commit()

        reset_url = (
            f"{settings.FRONTEND_URL}/auth/reset-password?token={raw_token}"
        )

        send_reset_email(user.email, reset_url)

    return {
        "message": "If that email is registered, we sent a reset link."
    }


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset = (
        db.query(PasswordReset)
        .filter(PasswordReset.token_hash == hash_reset_token(data.token))
        .first()
    )

    now = datetime.now(timezone.utc)

    if (
        reset is None
        or reset.used_at is not None
        or reset.expires_at < now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or expired",
        )

    user = db.query(User).filter(User.id == reset.user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or expired",
        )

    user.password_hash = hash_password(data.password)
    reset.used_at = now

    db.commit()

    return {
        "message": "Password updated"
    }
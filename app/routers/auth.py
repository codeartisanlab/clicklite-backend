from fastapi import APIRouter, Depends, HTTPException, status,Response
from sqlalchemy.orm import Session

from app.core.security import hash_password,verify_password,create_access_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, UserResponse,TokenResponse,LoginRequest


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
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

    return UserResponse(
        id=str(user.id),
        full_name=user.full_name,
        email=user.email
    )


# Login
@router.post(
    "/login"
)
def login(data: LoginRequest,response:Response, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(str(user.id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60,
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
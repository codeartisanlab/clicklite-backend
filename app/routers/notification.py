import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse, ReadAllResponse


import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.core.security import decode_access_token

sockets: dict[str, set[WebSocket]] = {}
main_loop: asyncio.AbstractEventLoop | None = None

def push_notification(user_id, payload) -> None:
    if main_loop is None:
        return
    message = payload.model_dump(mode="json")
    for socket in list(sockets.get(str(user_id), set())):
        asyncio.run_coroutine_threadsafe(
            socket.send_json(message),
            main_loop,
        )


def add_notification(
    db: Session,
    user_id: uuid.UUID,
    kind: str,
    message: str,
    link: str,
) -> None:
    notification=Notification(
            user_id=user_id,
            kind=kind,
            message=message,
            link=link,
            is_read=False,
        )

    db.add(notification)
    db.flush()
    push_notification(user_id, to_notification_response(notification))


def to_notification_response(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=str(notification.id),
        kind=notification.kind,
        message=notification.message,
        link=notification.link,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)


@router.websocket("/ws")
async def notifications_socket(websocket: WebSocket):
    global main_loop
    main_loop = asyncio.get_running_loop()

    token = websocket.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    user_id = payload.get("sub") if payload else None

    if not user_id:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    room = sockets.setdefault(str(user_id), set())
    room.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        room.discard(websocket)


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [to_notification_response(row) for row in rows]


@router.post(
    "/read-all",
    response_model=ReadAllResponse,
)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .all()
    )

    for row in rows:
        row.is_read = True

    db.commit()

    return ReadAllResponse(updated=len(rows))


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)

    return to_notification_response(notification)
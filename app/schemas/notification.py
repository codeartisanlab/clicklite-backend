from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    kind: str
    message: str
    link: str
    is_read: bool
    created_at: datetime


class ReadAllResponse(BaseModel):
    updated: int
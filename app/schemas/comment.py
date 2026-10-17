from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(
        min_length=1,
        max_length=1000
    )


class CommentResponse(BaseModel):
    id: str
    body: str
    task_id: str
    author_name: str
    created_at: datetime
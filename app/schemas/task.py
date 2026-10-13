from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200
    )
    description: str | None = None
    status: str = "todo"
    due_date: date | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    due_date: date | None
    project_id: str

class TaskStatusUpdate(BaseModel):
    status: Literal["todo", "in_progress", "done"]
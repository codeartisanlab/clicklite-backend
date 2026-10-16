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
    priority: Literal["low", "medium", "high"] = "medium"
    assignee: str | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    description: str | None = None
    status: Literal["todo", "in_progress", "done"] | None = None
    priority: Literal["low", "medium", "high"] | None = None
    assignee: str | None = None
    due_date: date | None = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None
    status: str
    priority: str
    assignee: str | None
    due_date: date | None
    project_id: str
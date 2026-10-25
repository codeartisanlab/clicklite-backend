from datetime import date,datetime
from typing import Literal

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200
    )
    description: str | None = None
    status: Literal["todo", "in_progress", "done"] = "todo"
    priority: Literal["low", "medium", "high"] = "medium"
    assignee: str | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
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
    updated_at:datetime


class TaskCalendarResponse(BaseModel):
    id: str
    title: str
    due_date: date
    status: str
    project_id: str
    project_name: str
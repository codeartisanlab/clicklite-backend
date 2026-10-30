from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TaskSentence(BaseModel):
    sentence: str = Field(min_length=3, max_length=300)


class TaskDraft(BaseModel):
    title: str
    description: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: date | None = None
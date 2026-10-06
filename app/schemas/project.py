from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )
    description: str | None = None
    workspace_id: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    workspace_id: str
    workspace_name:str | None = None
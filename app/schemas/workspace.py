from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    color: str = Field(
        min_length=4,
        max_length=20
    )


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    color: str
    owner_id: str
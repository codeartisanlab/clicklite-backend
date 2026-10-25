from pydantic import BaseModel


class SearchProject(BaseModel):
    id: str
    name: str
    workspace_name: str


class SearchTask(BaseModel):
    id: str
    title: str
    project_id: str
    project_name: str


class SearchResponse(BaseModel):
    projects: list[SearchProject]
    tasks: list[SearchTask]
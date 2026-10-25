from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.workspace import router as workspace_router
from app.routers.project import router as project_router
from app.routers.task import router as task_router
from app.routers.comment import router as comment_router
from app.routers.task import calendar_router
from app.routers.member import router as member_router
from app.routers.notification import router as notification_router
from app.routers.search import router as search_router


app = FastAPI(
    title="ClickLite API",
    description="API for ClickLite project management system",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    error = exc.errors()[0]
    field = error["loc"][-1]
    reason = error["msg"]

    return JSONResponse(
        status_code=422,
        content={"detail": f"{field}: {reason}"},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(workspace_router)
app.include_router(project_router)
app.include_router(task_router)
app.include_router(comment_router)
app.include_router(calendar_router)
app.include_router(member_router)
app.include_router(notification_router)
app.include_router(search_router)

@app.get("/")
def root():
    return {
        "message": "ClickLite API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
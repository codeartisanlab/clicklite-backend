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
from app.routers.member import invite_router
from app.routers.activity import router as activity_router
from app.routers.ai import router as ai_router
from app.core.config import settings


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

origins = [
    "http://localhost:3000",
    "https://clicklite-frontend.vercel.app",
]

if settings.FRONTEND_URL not in origins:
    origins.append(settings.FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(invite_router)
app.include_router(activity_router)
app.include_router(ai_router)

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
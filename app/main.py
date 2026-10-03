from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.workspace import router as workspace_router


app = FastAPI(
    title="ClickLite API",
    description="API for ClickLite project management system",
    version="1.0.0",
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
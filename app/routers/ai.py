import json
from datetime import date
from urllib import request as urlrequest
from urllib.error import HTTPError

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


from app.db.database import get_db
from app.models.comment import Comment
from app.routers.comment import get_owned_task

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.routers.task import load_my_day
from app.schemas.ai import TaskDraft, TaskSentence,CommentSummary,CommentSummaryRequest,DayPlan

import ssl
import certifi

router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)


def ask_groq(prompt: str) -> dict:
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI is not configured",
        )

    body = json.dumps({
        "model": "openai/gpt-oss-20b",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "user", "content": prompt},
        ],
    }).encode()

    req = urlrequest.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "ClickLite/1.0",
        },
    )

    try:
        context = ssl.create_default_context(cafile=certifi.where())
        with urlrequest.urlopen(req, timeout=20, context=context) as response:
            payload = json.loads(response.read().decode())
        raw = payload["choices"][0]["message"]["content"]
        return json.loads(raw)
    except (HTTPError, json.JSONDecodeError, KeyError, IndexError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The AI request failed",
        )


@router.post("/task", response_model=TaskDraft)
def draft_task(
    data: TaskSentence,
    current_user: User = Depends(get_current_user),
):
    prompt = (
        f"Today is {date.today().isoformat()}. "
        "Turn the sentence into one task. "
        "Return only JSON with title, description, priority, and due_date. "
        "priority must be low, medium, or high. "
        "due_date must be YYYY-MM-DD or null. "
        f"Sentence: {data.sentence.strip()}"
    )
    parsed = ask_groq(prompt)
    title = str(parsed.get("title") or "").strip()

    if len(title) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The AI reply had no title",
        )

    priority = parsed.get("priority")

    if priority not in ("low", "medium", "high"):
        priority = "medium"

    due_date = None
    raw_date = parsed.get("due_date")

    if isinstance(raw_date, str) and raw_date:
        try:
            due_date = date.fromisoformat(raw_date[:10])
        except ValueError:
            due_date = None

    description = parsed.get("description")

    if description is not None:
        description = str(description).strip() or None

    return TaskDraft(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
    )


@router.post("/comments/summary", response_model=CommentSummary)
def summarize_comments(
    data: CommentSummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = get_owned_task(db, data.project_id, data.task_id, current_user)

    rows = (
        db.query(Comment, User)
        .join(User, Comment.user_id == User.id)
        .filter(Comment.task_id == task.id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add a comment first",
        )

    lines = [
        f"{user.full_name}: {comment.body.strip()}"
        for comment, user in rows
    ]

    prompt = (
        "Summarize these task comments into one short note. "
        "Return only JSON with note. "
        "The note must be one or two sentences.\n"
        + "\n".join(lines)
    )

    parsed = ask_groq(prompt)
    note = str(parsed.get("note") or "").strip()

    if len(note) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The AI reply had no note",
        )

    return CommentSummary(note=note)


@router.post("/day", response_model=DayPlan)
def plan_my_day(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    due_rows, progress_rows = load_my_day(db, current_user)
    chosen = {}

    for task, project in due_rows + progress_rows:
        chosen[str(task.id)] = (task, project)

    if not chosen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nothing is due or in progress",
        )

    lines = []

    for task, project in chosen.values():
        due = task.due_date.isoformat() if task.due_date else "no date"
        lines.append(
            f"{task.title} in {project.name}, status {task.status}, due {due}"
        )

    prompt = (
        f"Today is {date.today().isoformat()}. "
        "Write one short plan for these tasks. "
        "Return only JSON with note. "
        "The note must be one or two sentences.\n"
        + "\n".join(lines)
    )

    parsed = ask_groq(prompt)
    note = str(parsed.get("note") or "").strip()

    if len(note) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The AI reply had no note",
        )

    return DayPlan(note=note)
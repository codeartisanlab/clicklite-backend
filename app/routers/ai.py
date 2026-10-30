import json
from datetime import date
from urllib import request as urlrequest
from urllib.error import HTTPError

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import TaskDraft, TaskSentence

import ssl
import certifi


router = APIRouter(
    prefix="/api/ai",
    tags=["AI"],
)


@router.post("/task", response_model=TaskDraft)
def draft_task(
    data: TaskSentence,
    current_user: User = Depends(get_current_user),
):
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI is not configured",
        )

    prompt = (
        f"Today is {date.today().isoformat()}. "
        "Turn the sentence into one task. "
        "Return only JSON with title, description, priority, and due_date. "
        "priority must be low, medium, or high. "
        "due_date must be YYYY-MM-DD or null. "
        f"Sentence: {data.sentence.strip()}"
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
    except HTTPError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The AI request failed",
        )

    raw = payload["choices"][0]["message"]["content"]
    parsed = json.loads(raw)

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
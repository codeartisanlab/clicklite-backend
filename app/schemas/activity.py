from datetime import datetime
from pydantic import BaseModel

class ActivityResponse(BaseModel):
    id: str
    user_name: str
    message: str
    link: str
    created_at: datetime
from pydantic import BaseModel
from pydantic import ConfigDict
from typing import List, Optional
from datetime import datetime


class TicketCreate(BaseModel):
    user_id: int
    title: str
    description: str
    tags: List[str] = []


class TicketRead(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    title: str
    description: str
    tags: List[str]

    model_config = ConfigDict(from_attributes=True)


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

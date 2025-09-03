from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ParseRequest(BaseModel):
    text: str

class ParseResult(BaseModel):
    title: str
    start: datetime
    end: Optional[datetime] = None

class EventCreate(BaseModel):
    title: str
    start: datetime
    end: Optional[datetime] = None
    raw_text: Optional[str] = None

class EventOut(BaseModel):
    id: int
    title: str
    start: datetime
    end: Optional[datetime] = None
    raw_text: Optional[str] = None

    model_config = {"from_attributes": True}
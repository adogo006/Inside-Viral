from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CrawlRelayRequest(BaseModel):
    gall_main_url: str = Field(..., description="dcinside gallery list url")
    days: int = Field(1, ge=1, description="collect target days")
    days_ago: int = Field(0, ge=0, description="start offset days ago")


class CrawlerCallbackPayload(BaseModel):
    request_id: str
    status: Literal["succeeded", "failed", "cancelled"]
    error_message: Optional[str] = None
    finished_at: Optional[datetime] = None
    saved_rows: Optional[int] = None


class RequestLogUpsert(BaseModel):
    request_id: str
    gall_main_url: str
    days: int
    days_ago: int
    status: str
    error_message: Optional[str] = None
    saved_rows: int = 0
    finished_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

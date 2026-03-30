from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone

import os
import uuid
import httpx


app = FastAPI(title="InsideViral API")

# NOTE: demo용 메모리 저장소. 운영에서는 Redis/DB로 교체하세요.
crawl_requests: dict[str, dict] = {}


class CrawlRelayRequest(BaseModel):
    gall_main_url: str = Field(..., description="dcinside gallery list url")
    days: int = Field(1, ge=1, description="collect target days")
    days_ago: int = Field(0, ge=0, description="start offset days ago")


class CrawlerCallbackPayload(BaseModel):
    request_id: str
    status: Literal["succeeded", "failed"]
    error_message: Optional[str] = None
    finished_at: Optional[str] = None
    saved_rows: Optional[int] = None


async def notify_user_or_admin(request_id: str, status: str, error_message: Optional[str] = None, saved_rows: Optional[int] = None):
    """콜백 수신 후 알림 훅. 기본은 로그 출력, 필요 시 웹훅으로 확장."""
    print(f"[NOTIFY] request_id={request_id} status={status} saved_rows={saved_rows} error={error_message}")
    webhook_url = os.getenv("ADMIN_WEBHOOK_URL")

    if not webhook_url:
        return

    payload = {
        "request_id": request_id,
        "status": status,
        "error_message": error_message,
        "saved_rows": saved_rows,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(webhook_url, json=payload)
    except Exception as exc:
        print(f"[NOTIFY] webhook failed: {exc}")


@app.get("/")
def read_root():
    return {"message": "Welcome to InsideViral API Server"}


@app.get("/crawl/{request_id}")
def get_crawl_status(request_id: str):
    request_data = crawl_requests.get(request_id)
    if request_data is None:
        raise HTTPException(status_code=404, detail="request_id not found")
    return request_data


@app.post("/crawl/callback")
async def crawl_callback(payload: CrawlerCallbackPayload):
    request_data = crawl_requests.get(payload.request_id)
    if request_data is None:
        raise HTTPException(status_code=404, detail="request_id not found")

    finished_at = payload.finished_at or datetime.now(timezone.utc).isoformat()
    request_data["status"] = payload.status
    request_data["error_message"] = payload.error_message
    request_data["finished_at"] = finished_at
    request_data["saved_rows"] = payload.saved_rows

    await notify_user_or_admin(payload.request_id, payload.status, payload.error_message, payload.saved_rows)
    return {"message": "callback accepted", "request_id": payload.request_id}


@app.post("/crawl")
async def request_api_crawling(payload: CrawlRelayRequest):
    crawler_url = os.getenv("CRAWLER_URL")
    if not crawler_url:
        raise HTTPException(status_code=500, detail="CRAWLER_URL is not configured")

    request_id = str(uuid.uuid4())
    body = {
        "url": payload.gall_main_url,
        "days": payload.days,
        "previous_days": payload.days_ago,
        "request_id": request_id,
        "callback_url": os.getenv("API_CALLBACK_URL"),
    }

    crawl_requests[request_id] = {
        "request_id": request_id,
        "status": "pending_dispatch",
        "gall_main_url": payload.gall_main_url,
        "days": payload.days,
        "days_ago": payload.days_ago,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "finished_at": None,
        "error_message": None,
        "saved_rows": 0,
    }

    endpoint = crawler_url.rstrip("/") + "/crawl"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=body)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else "crawler http error"
        raise HTTPException(status_code=502, detail=f"crawler rejected request: {detail}")
    except httpx.RequestError as exc:
        crawl_requests[request_id]["status"] = "dispatch_failed"
        crawl_requests[request_id]["error_message"] = str(exc)
        raise HTTPException(status_code=503, detail=f"crawler unavailable: {exc}")

    data = response.json()
    crawl_requests[request_id]["status"] = data.get("status", "queued")
    print(f"Crawl request({request_id}) successfully accepted by crawler")
    return {
        "message": "crawl request accepted",
        "api_request_id": request_id,
        "crawler_request_id": data.get("request_id", request_id),
        "status": data.get("status", "queued")
    }
     
    
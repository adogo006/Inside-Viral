from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, time, timezone, timedelta
from contextlib import asynccontextmanager

import os
import uuid
import httpx
from pydantic import ValidationError
from uuid import UUID

from schemas import CrawlRelayRequest, CrawlerCallbackPayload, RequestLogUpsert, ComputeAverageSentimentRequest
from DB_manager.models import RequestStatus
from api_crud import api_create_request_log, api_get_request_log, api_update_request_log
from DB_manager.database import SessionLocal, engine
from DB_manager import models
from sqlalchemy import select
from DB_manager.crud import compute_average_sentiment, get_historical_sentiments
from scheduler_runtime import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        
        stop_scheduler()


app = FastAPI(title="InsideViral API", lifespan=lifespan)

# CORS 설정: 브라우저의 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/crawl/healthcheck")
async def health_check():
    endpoint = os.getenv("CRAWLER_URL") + "healthcheck" if os.getenv("CRAWLER_URL") else None
    if not endpoint:       
        raise HTTPException(status_code=500, detail="CRAWLER_URL is not configured")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else "crawler error"
        raise HTTPException(status_code=502, detail=f"crawler error: {detail}")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail=f"crawler unavailable: {exc}")
    return {
        "message": "crawler healthcheck ok",
        "crawler_response": response.json(),
    }

@app.get("/crawl/{request_id}")
def get_crawl_status(request_id: UUID):
    db = SessionLocal()
    try:
        request_log = api_get_request_log(db, request_id)
        if request_log is None:
            raise HTTPException(status_code=404, detail="request_id not found")
        return {
            "request_id": request_log.request_id,
            "status": request_log.status,
            "gall_main_url": request_log.gall_main_url,
            "days": request_log.days,
            "days_ago": request_log.days_ago,
            "created_at": request_log.created_at.isoformat(),
            "finished_at": request_log.finished_at.isoformat() if request_log.finished_at else None,
            "error_message": request_log.error_message,
            "saved_rows": request_log.saved_rows,
        }
    finally:
        db.close()


@app.post("/crawl/callback")
async def crawl_callback(payload: CrawlerCallbackPayload):
    db = SessionLocal()
    try:
        # DB에서 기존 요청 로그 조회
        existing_log = api_get_request_log(db, payload.request_id)
        if existing_log is None:
            raise HTTPException(status_code=404, detail="request_id not found")

        # 콜백 데이터로 로그 업데이트
        finished_at = payload.finished_at or datetime.now(timezone.utc)
        updated_log = RequestLogUpsert(
            request_id=payload.request_id,
            gall_main_url=existing_log.gall_main_url,
            days=existing_log.days,
            days_ago=existing_log.days_ago,
            status=payload.status,
            error_message=payload.error_message,
            saved_rows=payload.saved_rows or 0,
            created_at=existing_log.created_at,
            finished_at=finished_at,
        )
        api_update_request_log(db, payload.request_id, updated_log)
        await notify_user_or_admin(payload.request_id, payload.status, payload.error_message, payload.saved_rows)
        #await request_nlp_assign_sentiment(payload.request_id)
        return {"message": "callback accepted", "request_id": payload.request_id}
    finally:
        db.close()

async def request_nlp_assign_sentiment(request_id: str | None = None):
    endpoint = os.getenv("NLP_URL") + "assign-sentiment" if os.getenv("NLP_URL") else None
    if not endpoint:
        print("[API] NLP_URL is not configured, skipping sentiment assignment")
        return
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json={"request_id": request_id})
            response.raise_for_status()
            data = response.json()
            print(f"[API] NLP request accepted: {data.get('nlp_request_id')}")
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text if exc.response is not None else "NLP error"
        print(f"[API] NLP assign sentiment error: {detail}")
    except httpx.RequestError as exc:
        print(f"[API] NLP assign sentiment unavailable: {exc}")

    return {"message": "NLP assign sentiment task requested"}
    

@app.post("/crawl")
async def request_api_crawling(payload: CrawlRelayRequest):
    crawler_url = os.getenv("CRAWLER_URL")
    if not crawler_url:
        raise HTTPException(status_code=500, detail="CRAWLER_URL is not configured")

    db = SessionLocal()
    try:
        request_id = str(uuid.uuid4())
        body = {
            "gall_main_url": payload.gall_main_url,
            "days": payload.days,
            "days_ago": payload.days_ago,
            "request_id": request_id,
            "callback_url": os.getenv("API_CALLBACK_URL"),
        }

        # 초기 요청 로그 DB에 생성
        print(f"[API] request_id={request_id} request log 생성 시도")
        try:
            initial_log = RequestLogUpsert(
                request_id=request_id,
                gall_main_url=payload.gall_main_url,
                days=payload.days,
                days_ago=payload.days_ago,
                status=RequestStatus.PENDING.value,
                error_message=None,
                saved_rows=0,
                finished_at=None,
            )
        except ValidationError as exc:
            print(f"[API] request_id={request_id} RequestLogUpsert 검증 실패: {exc}")
            raise HTTPException(
                status_code=500,
                detail={"message": "request log schema validation failed", "errors": exc.errors()},
            )

        models.Base.metadata.create_all(bind=engine)
        create_result = api_create_request_log(db, initial_log)
        if create_result != 0:
            print(f"[API] request_id={request_id} request log 저장 실패로 요청 중단")
            raise HTTPException(status_code=500, detail="failed to create request log")
        endpoint = crawler_url.rstrip("/") + "/crawl"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, json=body)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text if exc.response is not None else "crawler http error"
            # 실패 상태를 DB에 업데이트
            failed_log = RequestLogUpsert(
                request_id=request_id,
                gall_main_url=payload.gall_main_url,
                days=payload.days,
                days_ago=payload.days_ago,
                status=RequestStatus.DISPATCH_FAILED.value,
                error_message=str(exc),
                saved_rows=0,
                finished_at=datetime.now(timezone.utc),
            )
            api_update_request_log(db, request_id, failed_log)
            raise HTTPException(status_code=502, detail=f"crawler rejected request: {detail}")
        except httpx.RequestError as exc:
            # 요청 실패 상태를 DB에 업데이트
            failed_log = RequestLogUpsert(
                request_id=request_id,
                gall_main_url=payload.gall_main_url,
                days=payload.days,
                days_ago=payload.days_ago,
                status=RequestStatus.DISPATCH_FAILED.value,
                error_message=str(exc),
                saved_rows=0,
                finished_at=datetime.now(timezone.utc),
            )
            api_update_request_log(db, request_id, failed_log)
            raise HTTPException(status_code=503, detail=f"crawler unavailable: {exc}")

        # 크롤러 응답으로 상태 업데이트
        data = response.json()
        status_log = RequestLogUpsert(
            request_id=request_id,
            gall_main_url=payload.gall_main_url,
            days=payload.days,
            days_ago=payload.days_ago,
            status=data.get("status", RequestStatus.RUNNING.value),
            error_message=None,
            saved_rows=0,
            finished_at=None,
        )
        api_update_request_log(db, request_id, status_log)
        print(f"Crawl request({request_id}) successfully accepted by crawler")
        return {
            "message": "crawl request accepted",
            "request_id": request_id,
            "status": data.get("status", RequestStatus.RUNNING.value),
        }
    finally:
        db.close()

@app.post("/sentiment/compute")
def request_compute_average_sentiment(payload: ComputeAverageSentimentRequest):
    """특정 갤러리 날짜에 대해 평균 감성 지수를 계산하고 저장합니다."""
    db = SessionLocal()
    try:
        average = compute_average_sentiment(db, payload.gall_id, payload.target_date, payload.period)
        return {
            "message": "compute_average_sentiment completed",
            "gall_id": payload.gall_id,
            "target_date": payload.target_date.isoformat(),
            "period": payload.period,
            "average_sentiment": average,
        }
    finally:
        db.close()


# POST https://api:8000/crawl/cancel/
@app.post("/crawl/cancel/{request_id}")
async def cancel_api_crawling(request_id: str):
    """크롤링 요청을 강제 종료합니다."""
    crawler_url = os.getenv("CRAWLER_URL")
    if not crawler_url:
        raise HTTPException(status_code=500, detail="CRAWLER_URL is not configured")

    db = SessionLocal()
    try:
        # 요청 로그 확인
        request_log = api_get_request_log(db, request_id)
        if request_log is None:
            raise HTTPException(status_code=404, detail="request_id not found")

        # 이미 종료되었거나 취소 중인 작업인지 확인
        terminal_statuses = [
            RequestStatus.SUCCEEDED.value,
            RequestStatus.FAILED.value,
            RequestStatus.CANCELLED.value,
            RequestStatus.DISPATCH_FAILED.value,
            RequestStatus.CANCELLING.value
        ]
        if request_log.status in terminal_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel request with status '{request_log.status}'. Only running or pending requests can be cancelled."
            )

        # 크롤러 서버에 취소 요청
        endpoint = crawler_url.rstrip("/") + f"/cancel/{request_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(endpoint)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text if exc.response is not None else "crawler error"
            raise HTTPException(status_code=502, detail=f"crawler error: {detail}")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"crawler unavailable: {exc}")

        # DB 상태를 'cancelling'으로 업데이트
        cancel_log = RequestLogUpsert(
            request_id=request_id,
            gall_main_url=request_log.gall_main_url,
            days=request_log.days,
            days_ago=request_log.days_ago,
            status=RequestStatus.CANCELLING.value,
            error_message=None,
            saved_rows=request_log.saved_rows,
            finished_at=None,
        )
        api_update_request_log(db, request_id, cancel_log)
        print(f"[API] request_id={request_id} cancellation requested")

        return {
            "message": "crawl request cancellation requested",
            "request_id": request_id,
            "status": "cancelling"
        }
    finally:
        db.close()

@app.get("/sentiment/history")
def read_sentiment_history(gall_id: str, period: str = "7D"):
    db = SessionLocal()
    try:
        days_map = {"1D": 1, "7D": 7, "1M": 30, "1Y": 365}
        days = days_map.get(period, 7)
        
        # [수정] 시작 날짜의 시간을 00:00:00으로 설정하여 당일 데이터 포함
        now = datetime.now(timezone.utc)
        start_date = datetime.combine(now.date() - timedelta(days=days), time.min).replace(tzinfo=timezone.utc)
        
        print(f"조회 시작: {gall_id} (범위: {start_date} ~ 현재)")

        stmt = select(models.AverageSentimentForOneDay).where(
            models.AverageSentimentForOneDay.gall_id == gall_id,
            models.AverageSentimentForOneDay.date >= start_date
        ).order_by(models.AverageSentimentForOneDay.date.asc())
        
        result = db.execute(stmt).scalars().all()
        
        # Lightweight Charts 형식에 맞춰 변환 (time은 'YYYY-MM-DD' 문자열)
        chart_data = [
            {
                "time": r.date.strftime("%Y-%m-%d"), 
                "value": float(r.average_sentiment)
            } for r in result
        ]
        
        print(f"조회 완료: {len(chart_data)}개의 데이터를 찾았습니다.")
        return chart_data
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import os
from datetime import datetime, timezone
import httpx

from DB_manager.database import engine, SessionLocal
from DB_manager import models
from Crawling import startCrawler
from crud_crawling import export_to_txt, delete_whitespace_word

app = FastAPI(title= 'inside-viral Crawler Service')

class CrawlerRequest(BaseModel):
    url: str
    days: int
    previous_days: int = 0
    request_id: str | None = None
    callback_url: str | None = None


async def send_callback(
    callback_url: str | None,
    request_id: str,
    status: str,
    error_message: str | None = None,
    saved_rows: int | None = None,
):
    if callback_url is None:
        callback_url = os.getenv('API_CALLBACK_URL') if os.getenv('API_CALLBACK_URL') else None

    if callback_url is None:
        print(f"(Crawler)[{request_id}] callback URL이 없어 완료 신호를 생략합니다.")
        return

    payload = {
        'request_id': request_id,
        'status': status,
        'error_message': error_message,
        'finished_at': datetime.now(timezone.utc).isoformat(),
        'saved_rows': saved_rows,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(callback_url, json=payload)
            response.raise_for_status()
        print(f"(Crawler)[{request_id}] callback 전송 완료: {status}")
    except Exception as exc:
        print(f"(Crawler)[{request_id}] callback 전송 실패: {exc}")


async def task_crawl_and_save(url: str, days: int, previousDays: int, request_id: str, callback_url: str | None = None):
    try:
        models.Base.metadata.create_all(bind=engine)
        print(f'(Crawler)[{request_id}] 크롤링을 시작합니다.')
        isError, save_count = await startCrawler(url, days, previousDays, request_id)
        saved_rows = save_count * 100
        print(f'(Crawler)[{request_id}] 크롤링을 종료합니다.')
        if isError == -1:
            await send_callback(callback_url, request_id, 'failed', 'Crawling failed', saved_rows)
        else:
            await send_callback(callback_url, request_id, 'succeeded', None, saved_rows)
    except Exception as exc:
        print(f'(Crawler)[{request_id}] 크롤링 실패: {exc}')
        await send_callback(callback_url, request_id, 'failed', str(exc))


@app.get('/')
def health_check():
    return {'message': 'Crawler service is running'}


@app.post('/crawl')
async def request_crawl(payload: CrawlerRequest):
    request_id = payload.request_id or str(uuid.uuid4())
    if payload.days < 1:
        raise HTTPException(status_code=400, detail='days must be >= 1')
    if payload.previous_days < 0:
        raise HTTPException(status_code=400, detail='previous_days must be >= 0')

    asyncio.create_task(
        task_crawl_and_save(
            payload.url,
            payload.days,
            payload.previous_days,
            request_id,
            payload.callback_url,
        )
    )
    return {
        'message': 'crawl task queued',
        'request_id': request_id,
        'status': 'queued'
    }



if __name__ == '__main__':
    asyncio.run(task_crawl_and_save('https://gall.dcinside.com/mgallery/board/lists/?id=stockus', 30, 0, str(uuid.uuid4())))
    delete_whitespace_word(SessionLocal)
    #export_to_txt()
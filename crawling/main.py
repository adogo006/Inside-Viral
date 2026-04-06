import asyncio
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uuid
import os
from datetime import datetime, timezone
import httpx
import importlib

from DB_manager.database import engine, SessionLocal
from DB_manager import models
from Crawling import startCrawler
from crud_crawling import export_to_txt, delete_whitespace_word

try:
    from crawling import runtime_state
except ImportError:
    runtime_state = importlib.import_module('runtime_state')

app = FastAPI(title= 'inside-viral Crawler Service')

# request_id -> Task 매핑을 위한 dict
active_crawl_tasks: dict[str, asyncio.Task] = {}

class CrawlerRequest(BaseModel):
    gall_main_url: str
    days: int
    days_ago: int = 0
    request_id: str | None = None
    callback_url: str | None = None
class CrawlerCallbackPayload(BaseModel):
    request_id: str
    status: Literal["succeeded", "failed"]
    error_message: Optional[str] = None
    finished_at: Optional[datetime] = None
    saved_rows: Optional[int] = None

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
    runtime_state.active_tasks += 1
    try:
        models.Base.metadata.create_all(bind=engine)
        print(f'(Crawler)[{request_id}] 크롤링을 시작합니다.')
        isError, save_count = await startCrawler(url, days, previousDays, request_id)
        saved_rows = save_count * 100
        print(f'(Crawler)[{request_id}] 크롤링을 종료합니다.')
        if isError == -1:
            await send_callback(callback_url, request_id, 'failed', 'Crawling failed', saved_rows)
        else:
            await send_callback(callback_url, request_id, 'succeeded', 'Crawling succeeded', saved_rows)
    except asyncio.CancelledError:
        print(f'(Crawler)[{request_id}] 크롤링이 사용자에 의해 강제 종료되었습니다.')
        await send_callback(callback_url, request_id, 'cancelled', 'Crawling cancelled by user')
    except Exception as exc:
        print(f'(Crawler)[{request_id}] 크롤링 실패: {exc}')
        await send_callback(callback_url, request_id, 'failed', str(exc))
    finally:
        runtime_state.active_tasks -= 1
        active_crawl_tasks.pop(request_id, None)
        print(f"(Crawler)[{request_id}] 작업 종료. 현재 활성 작업 수: {runtime_state.active_tasks}/{runtime_state.MAX_CONCURRENT_TASKS}")


@app.get('/healthcheck')
def health_check():
    task_list ="\n".join(active_crawl_tasks.keys())

    return {'message': (f'Crawler service is running({runtime_state.active_tasks}/{runtime_state.MAX_CONCURRENT_TASKS})'
                         '현재 활성 프로세스 상태'
                        f'{task_list}')}


@app.post('/cancel/{request_id}')
async def cancel_crawl(request_id: str):
    """특정 request_id의 크롤링 작업을 강제 종료합니다."""
    if request_id not in active_crawl_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'message': f'request_id {request_id} not found', 'request_id': request_id}
        )
    
    task = active_crawl_tasks[request_id]
    if task.done():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'message': f'request_id {request_id} is already finished', 'request_id': request_id}
        )
    
    task.cancel()
    print(f'(Crawler)[{request_id}] 취소 신호 전송됨.')
    return {
        'message': 'crawl task cancellation requested',
        'request_id': request_id,
        'status': 'cancelling'
    }


@app.post('/crawl')
async def request_crawl(payload: CrawlerRequest):
    if runtime_state.active_tasks >= runtime_state.MAX_CONCURRENT_TASKS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={'message': f"Too many concurrent tasks. Currently {runtime_state.active_tasks}/{runtime_state.MAX_CONCURRENT_TASKS} tasks running.",
                    'request_id': payload.request_id, 'status': 'failed'}
           )

    task = asyncio.create_task(
        task_crawl_and_save(
            payload.gall_main_url,
            payload.days,
            payload.days_ago,
            payload.request_id,
            payload.callback_url,
        )
    )
    active_crawl_tasks[payload.request_id] = task
    return {
        'message': f'crawl task running {runtime_state.active_tasks}/{runtime_state.MAX_CONCURRENT_TASKS}',
        'request_id': payload.request_id,
        'status': 'running'
    }



if __name__ == '__main__':
    asyncio.run(task_crawl_and_save('https://gall.dcinside.com/mgallery/board/lists/?id=stockus', 30, 0, str(uuid.uuid4())))
    delete_whitespace_word(SessionLocal)
    #export_to_txt()
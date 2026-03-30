from fastapi import FastAPI, Depends, HTTPException
from DB_manager.database import SessionLocal # 기존에 만드신 DB 설정 파일
from crawling.main import task_crawl_and_save

import uuid # 각 요청별 고유 id 생성을 위한 라이브러리
import httpx
import asyncio
import os

app = FastAPI(title="InsideViral API")
#insideViral-net 전용 내부포트 URL
# DB 세션 의존성 주입 (매 요청마다 DB 연결/해제 관리)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to InsideViral API Server"}


# 2. 크롤링 시작 명령 (POST 요청)
@app.post("/crawl/{gall_main_url}")
# /crawl/{gall_main_url}?days=x&days_ago=y
async def request_api_crawling(gall_main_url: str, days: int =1, days_ago: int = 0):
    request_id = str(uuid.uuid4())
    query_params = {
        "gall_main_url" : gall_main_url,
        "days" : days,
        "days_ago" : days_ago,
        "request_id": request_id
    }

    async def send_to_crawler():
        async with httpx.AsyncClient() as client:    
            try:
                response = await client.post(os.getenv('CRAWLER_URL'), '/crawl/', params= query_params, timeout= None)
                if response.status_code == 200:
                        response_request_id = response.json()["request_id"]
                        if response_request_id == request_id:
                            print(f"요청이 성공적으로 크롤링 컨테이너에 수신되었습니다")
                else:
                    print(f"에러 {response.status_code}가 발생하여 요청 {request_id}을 크롤링 컨테이너에 전송하지 못했습니다")
            except Exception as e:
                print(f"크롤링 요청 실패 {e}")

            # except httpx.HTTPStatusError as e:
            #     # 상대 컨테이너 오류 응답
            #     raise HTTPException(status_code=e.response.status_code, detail="컨테이너 통신 오류")
            # except httpx.RequestError:
            #     # 연결 자체가 안 되는 경우 (컨테이너가 꺼져있을 때 등)
            #     raise HTTPException(status_code=503, detail="크롤러 서비스에 연결할 수 없습니다.")

async with httpx.AsyncClient() as client:
    try: 
        response = await client.post(os.getenv('CRAWLER_URL'), '/crawl', params=)
    
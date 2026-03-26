from fastapi import FastAPI, Depends, HTTPException
from DB_manager.database import SessionLocal # 기존에 만드신 DB 설정 파일
from crawling.main import task_crawl_and_save

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

# 1. 특정 갤러리의 데이터 가져오기 (예: 공포 지수 산출용)
# @app.get("/words/{gall_id}", response_model=List[schemas.Word])
# def get_gallery_data(gall_id: str, db: Session = Depends(get_db)):
#     data = db.query(models.Word).filter(models.Word.gallId == gall_id).all()
#     if not data:
#         raise HTTPException(status_code=404, detail="Gallery data not found")
#     return data

# 2. 크롤링 시작 명령 (POST 요청)
@app.post("/crawl/{gall_main_url}")
# /crawl/{gall_main_url}?days=x&days_ago=y
async def request_crawling(gall_main_url: str, days: int =1, days_ago: int = 0):
    query_params = {
        "gall_main_url" : gall_main_url,
        "days" : days,
        "days_ago" : days_ago
    }

    async with httpx.AsyncClient() as client:    
        try:
            response = await client.get(os.getenv('CRAWLER_URL'), params= query_params, timeout= 10.0)
        
            response.raise_for_status()
            
            return response.json()
        
        except httpx.HTTPStatusError as e:
            # 상대 컨테이너 오류 응답
            raise HTTPException(status_code=e.response.status_code, detail="컨테이너 통신 오류")
        except httpx.RequestError:
            # 연결 자체가 안 되는 경우 (컨테이너가 꺼져있을 때 등)
            raise HTTPException(status_code=503, detail="크롤러 서비스에 연결할 수 없습니다.")

    return {"status": "success", "message": f"Crawling started for {gall_main_url}"}
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .database import SessionLocal # 기존에 만드신 DB 설정 파일
from . import models, schemas    # 모델과 데이터 규격

app = FastAPI(title="InsideViral API")

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
@app.get("/words/{gall_id}", response_model=List[schemas.Word])
def get_gallery_data(gall_id: str, db: Session = Depends(get_db)):
    data = db.query(models.Word).filter(models.Word.gallId == gall_id).all()
    if not data:
        raise HTTPException(status_code=404, detail="Gallery data not found")
    return data

# 2. 크롤링 시작 명령 (POST 요청)
@app.post("/crawl/{gall_id}")
def start_crawling(gall_id: str):
    # 여기서 크롤링 컨테이너에 신호를 보내는 로직이 들어갑니다.
    return {"status": "success", "message": f"Crawling started for {gall_id}"}
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from DB_manager.database import engine, SessionLocal
from DB_manager import models
import crud_NLP
from KeywordExtractor import main

app = FastAPI(title= 'inside-viral NLP Service')

def extract_keyword():
    db = SessionLocal()
    # try/finally 문을 사용해야 에러 발생시에도 session을 닫을 수 있음
    try:
        sentences = crud_NLP.get_words(db)
        weights = main(sentences)
        crud_NLP.update_weights(db, weights)
    finally:
        db.close()

def assign_sentiment():
    db = SessionLocal()
    try:
        # TODO: SentimentAnalyzer 연결
        pass
    finally:
        db.close()
    
# @app.sadsadsad(/KE), @app.sadsadsad(/SA) 이런식으로 api 요청 구분 가능
# 일단은 def 형식으로 작성
if __name__ == '__main__':
    extract_keyword()
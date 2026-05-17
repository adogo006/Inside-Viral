from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from DB_manager.database import engine, SessionLocal
from DB_manager import models
import asyncio

import crud_NLP, KeywordExtractor, SentimentAnalyzer

class NlpRequestPayload(BaseModel):
    request_id: str | None = None  # 크롤링 request_id 또는 None
    
app = FastAPI(title='inside-viral NLP Service')

@app.get('/healthcheck')
async def health_check():
    return {'message': 'NLP service is running'}
    
app = FastAPI(title='inside-viral NLP Service')

@app.get('/healthcheck')
async def health_check():
    return {'message': 'NLP service is running'}

@app.post('/extract-keyword')
async def extract_keyword():
    try:
        await do_extract_keyword()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {'status': 'success', 'message': 'Keywords extracted successfully'}


# asyncio.Lock()으로 동시 호출 방지 락 설정 필요?
async def do_extract_keyword():
    def _sync_work():
        db = SessionLocal()
        try:
            models.Base.metadata.create_all(bind=engine)
            sentences = crud_NLP.get_primary_sentences(db)
            sentence_texts = [sentence.wordContent for sentence in sentences]
            weights = KeywordExtractor.main(sentence_texts)
            crud_NLP.update_weights(db, weights)
        finally:
            db.close()

    await asyncio.to_thread(_sync_work)


@app.post('/assign-sentiment')
async def assign_sentiment(payload: NlpRequestPayload, background_tasks: BackgroundTasks):
    nlp_request_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        # NLP 요청 로그 생성
        nlp_log = models.NlpRequestLog(
            request_id=nlp_request_id,
            status=models.NlpRequestStatus.PENDING
        )
        db.add(nlp_log)
        db.commit()
        
        # 백그라운드에서 작업 수행
        background_tasks.add_task(do_assign_sentiment_async, nlp_request_id, payload.request_id)
        
        return {'status': 'accepted', 'nlp_request_id': nlp_request_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

async def do_assign_sentiment_async(nlp_request_id: str, crawl_request_id: str | None):
    db = SessionLocal()
    try:
        # 상태 RUNNING으로 업데이트
        nlp_log = db.query(models.NlpRequestLog).filter(models.NlpRequestLog.request_id == nlp_request_id).first()
        if nlp_log:
            nlp_log.status = models.NlpRequestStatus.RUNNING
            db.commit()
        
        # 실제 작업 수행
        sentences = crud_NLP.get_sentences(db, crawl_request_id or "null")
        weights = {weight.word: weight.weight for weight in crud_NLP.get_weights(db)}
        results = SentimentAnalyzer.main(sentences, weights)
        crud_NLP.update_sentiment(db, results)
        
        # 상태 SUCCEEDED로 업데이트
        if nlp_log:
            nlp_log.status = models.NlpRequestStatus.SUCCEEDED
            nlp_log.processed_sentences = len(results)
            nlp_log.finished_at = datetime.now(timezone.utc)
            db.commit()
    except Exception as e:
        # 상태 FAILED로 업데이트
        if nlp_log:
            nlp_log.status = models.NlpRequestStatus.FAILED
            nlp_log.error_message = str(e)
            nlp_log.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

@app.get('/nlp/status/{nlp_request_id}')
async def get_nlp_status(nlp_request_id: str):
    db = SessionLocal()
    try:
        nlp_log = db.query(models.NlpRequestLog).filter(models.NlpRequestLog.request_id == nlp_request_id).first()
        if not nlp_log:
            raise HTTPException(status_code=404, detail="NLP request not found")
        
        return {
            "nlp_request_id": nlp_log.request_id,
            "status": nlp_log.status,
            "processed_sentences": nlp_log.processed_sentences,
            "created_at": nlp_log.created_at.isoformat(),
            "finished_at": nlp_log.finished_at.isoformat() if nlp_log.finished_at else None,
            "error_message": nlp_log.error_message,
        }
    finally:
        db.close()
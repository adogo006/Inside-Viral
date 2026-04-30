from fastapi import FastAPI, HTTPException

from DB_manager.database import engine, SessionLocal
from DB_manager import models
import asyncio

import crud_NLP, KeywordExtractor, SentimentAnalyzer
from pydantic import BaseModel

class CrawlerRequestPayload(BaseModel):
    request_id: str
    
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
async def assign_sentiment(payload: CrawlerRequestPayload):
    request_id = payload.request_id
    try:
        await do_assign_sentiment(request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {'status': 'success', 'message': 'Sentiments assigned successfully'}
    

async def do_assign_sentiment(id: str):
    def _sync_work():
        db = SessionLocal()
        try:
            models.Base.metadata.create_all(bind=engine)
            sentences = crud_NLP.get_sentences(db, id)
            weights = {weight.word: weight.weight for weight in crud_NLP.get_weights(db)}
            results = SentimentAnalyzer.main(sentences, weights)
            crud_NLP.update_sentiment(db, results)
        finally:
            db.close()
    
    await asyncio.to_thread(_sync_work)
from fastapi import FastAPI, HTTPException

from DB_manager.database import engine, SessionLocal
from DB_manager import models
import crud_NLP, KeywordExtractor, SentimentAnalyzer

app = FastAPI(title='inside-viral NLP Service')

@app.get('/healthcheck')
def health_check():
    return {'message': 'NLP service is running'}

@app.post('/extract-keyword')
def extract_keyword():
    db = SessionLocal()
    try:
        models.Base.metadata.create_all(bind=engine)
        sentences = crud_NLP.get_sentences(db)
        sentence_texts = [sentence.wordContent for sentence in sentences]
        weights = KeywordExtractor.main(sentence_texts)
        crud_NLP.update_weights(db, weights)
        return {'status': 'success',
                'message': 'Keywords extracted successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.post('/assign-sentiment')
def assign_sentiment():
    db = SessionLocal()
    try:
        models.Base.metadata.create_all(bind=engine)
        sentences = crud_NLP.get_sentences(db)
        weights = {weight.word: weight.weight for weight in crud_NLP.get_weights(db)}
        results = SentimentAnalyzer.main(sentences, weights)
        crud_NLP.update_sentiment(db, results)
        return {'status': 'success',
                'message': 'Sentiments assigned successfully'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

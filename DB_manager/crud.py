#CREATE, READ, DELETE, 등 핵심 로직
from sqlalchemy.orm import Session
from sqlalchemy import DateTime, func
from datetime import datetime, timedelta
import models


# 1. CREATE 기능
def create_word_entry(db: Session, gall_id: str, up_date: DateTime, word_content: str, sentiment_score: float = 0.0):
    db_word = models.Word(
        gallId = gall_id,
        date = up_date,
        wordContent = word_content,
        sentiment = sentiment_score
    )
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word

# 2. READ 기능: 데이터 전체 조회
def get_words(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Word).offset(skip).limit(limit).all()

# 3. 특정조건 조회 함수
def get_words_gallId(db: Session, gall_id: str, limit: int = 100):
    return db.query(models.Word).filter(models.Word.gallId == gall_id).limit(limit).all()

def get_words_date(db: Session, gall_id: str, days: int = 1):
    dt = datetime.now() - timedelta(days= days)
    return db.query(models.Word).filter(models.Word.gallId == gall_id).filter(models.Word.date >= dt).all()

# 4. DELETE 기능: 쿼리 삭제 기능
def delete_word(db: Session, word_id: int):
    db_word = db.query(models.Word).filter(models.Word.id == word_id).first()
    if db_word:
        db.delete(db_word)
        db.commit()
        return True
    else:
        return False

# 5. AverageSentimentForOneDay CRUD
def create_average_sentiment(db: Session, gall_id: str, date: DateTime, average_sentiment: float):
    """하루 평균 감정지수 저장 (upsert)"""
    existing = db.query(models.AverageSentimentForOneDay).filter(
        models.AverageSentimentForOneDay.gall_id == gall_id,
        models.AverageSentimentForOneDay.date == date
    ).first()

    if existing:
        existing.average_sentiment = average_sentiment
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_entry = models.AverageSentimentForOneDay(
            gall_id=gall_id,
            date=date,
            average_sentiment=average_sentiment
        )
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry

def get_average_sentiments(
    db: Session,
    gall_id: str,
    days: int = 7
):
    """특정 갤러리의 최근 N일치 평균 감정지수 조회"""
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return db.query(models.AverageSentimentForOneDay).filter(
        models.AverageSentimentForOneDay.gall_id == gall_id,
        models.AverageSentimentForOneDay.date >= dt
    ).order_by(models.AverageSentimentForOneDay.date.asc()).all()

def get_average_sentiments_grouped(
    db: Session,
    gall_id: str,
    days: int = 7
):
    """聚合된 기간별 평균 감정지수 조회 (일별/주별/월별)"""
    from sqlalchemy import extract

    dt = datetime.now(timezone.utc) - timedelta(days=days)

    results = db.query(
        models.AverageSentimentForOneDay.date,
        models.AverageSentimentForOneDay.average_sentiment
    ).filter(
        models.AverageSentimentForOneDay.gall_id == gall_id,
        models.AverageSentimentForOneDay.date >= dt
    ).order_by(models.AverageSentimentForOneDay.date.asc()).all()

    return results

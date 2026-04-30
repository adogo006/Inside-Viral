#CREATE, READ, DELETE, 등 핵심 로직
from sqlalchemy.orm import Session
from sqlalchemy import DateTime, func, select
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timedelta, timezone
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

def compute_average_sentiment(db: Session, gall_id: str, target_date: datetime, period: int = 1):
    start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=timezone.utc)
    current_date = start_date
    next_date = start_date + timedelta(days=period)
    average_sentiment = 0.0

    try:
        while current_date < next_date:
            day_end = current_date + timedelta(days=1)
            stmt = select(func.avg(models.Word.sentiment)).where(
                models.Word.gallId == gall_id,
                models.Word.date >= current_date,
                models.Word.date < day_end,
                models.Word.state == models.ProcessState.COMPLETED,
            )
            average_sentiment = db.execute(stmt).scalar_one_or_none()
            if average_sentiment is None:
                average_sentiment = 0.0

            upsert_stmt = insert(models.AverageSentimentForOneDay).values(
                gall_id=gall_id,
                date=current_date,
                average_sentiment=average_sentiment,
            ).on_conflict_do_update(
                index_elements=["gall_id", "date"],
                set_={"average_sentiment": average_sentiment},
            )
            db.execute(upsert_stmt)

            current_date += timedelta(days=1)

        db.commit()
        print(f"Complete compute average sentiment for gall_id={gall_id} from {start_date} to {next_date}")
        return average_sentiment
    except Exception as exc:
        db.rollback()
        print(f"Failed compute average sentiment for gall_id={gall_id}: {exc!r}")
        raise
    
def delete_low_priority_words(db: Session, threshold: int = 1000):
    total_count = db.query(models.WeightInWord).count()
    if total_count > threshold:
        delete_count = total_count - threshold
        select_stmt = (select(models.WeightInWord.id)
                            .order_by(models.WeightInWord.update_count.asc()).limit(delete_count)
        )
        target_ids = db.execute(select_stmt).scalars().all()

        if target_ids:
            delete_stmt = (models.WeightInWord.__table__.delete().where(models.WeightInWord.id.in_(target_ids)))
            db.execute(delete_stmt)
            db.commit()
            print(f"{delete_count} 개의 낮은 우선순위 단어 삭제 완료!")
            return delete_count
        
    print("삭제할 단어가 없습니다.")
    return 0

def get_request_status(db : Session, request_id: str) -> str | None:
        request_log = (
            db.query(models.RequestLog)
            .filter(models.RequestLog.request_id == request_id)
            .first()
        )
        if request_log is None:
            return None
        return request_log.status

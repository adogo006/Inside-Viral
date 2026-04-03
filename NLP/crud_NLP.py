#CREATE, READ, DELETE, 등 핵심 로직
from sqlalchemy.orm import Session
from sqlalchemy import DateTime
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

def get_words(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Word).offset(skip).limit(limit).all()

def update_weights(db: Session, weights: dict):
    for word, weight in weights.items():
        existing = db.query(models.WeightInWord).filter(models.WeightInWord.word == word).first()
        if existing:
            # 학습할 때마다 weight를 갱신해주야 하는데, 적용 방법의 대한 생각 필요
            existing.weight = weight
        else:
            db.add(models.WeightInWord(word=word, weight=weight))
    db.commit()

def cleanup_duplicate_words(db: Session):
    # 중복 데이터 삭제 함수(gallId, date, wordContent 같을 시)
    query = text("""
        DELETE FROM words
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY "gallId", "wordContent", "date" 
                           ORDER BY id
                       ) as row_num
                FROM words
            ) t
            WHERE t.row_num > 1
        );
    """)
    try:
        result = db.execute(query)
        db.commit()
        print(f"클린업 완료: 총 {result.rowcount}개의 중복 행이 삭제되었습니다.")
        return 
    except Exception as e:
        db.rollback()
        print(f"클린업 중 오류 발생: {e}")
        return 
    
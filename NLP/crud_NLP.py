#CREATE, READ, DELETE, 등 핵심 로직
from sqlalchemy.orm import Session
from sqlalchemy import DateTime
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import insert
import DB_manager.models as models

def get_primary_sentences(db: Session):
    sentences = db.query(models.Word).filter(models.Word.state == "PENDING").filter(models.Word.learning_state == "PENDING").all()
    for sentence in sentences:
        sentence.state = models.LearningState.COMPLETED
    db.commit()
    return sentences

# 크롤링 종료 후 받는 요청과 스케쥴러에서 주기적으로 하는 요청을 구분 -> 비동기화로 사용했을 때 꼬임을 방지
def get_sentences(db: Session, request_id: str):
    if(request_id == "null"):
        return db.query(models.Word).filter(models.Word.state == "PENDING").all()
    else:
        return db.query(models.Word).filter(models.Word.request_id == request_id).filter(models.Word.state == "PENDING").all()

def get_weights(db: Session):
    return db.query(models.WeightInWord).all()

def update_weights(db: Session, weight_list: list[dict]):
    if not weight_list:
        return 0

    normalized_weight_list = [
        {"word": item["word"], "weight": float(item["weight"])}
        for item in weight_list
    ]
    stmt = insert(models.WeightInWord).values(normalized_weight_list)
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=['word'],
        set_={'weight': (models.WeightInWord.weight * 4 / 5) + (stmt.excluded.weight * 1 / 5),
              'update_count': models.WeightInWord.update_count + 1}
    )

    try:
        db.execute(upsert_stmt)
        db.commit()
        print("데이터 저장 완료!")
        return 0
    except Exception as e:
        db.rollback()
        print(f"save_in_weights: 오류 발생: {e}")
        return -1

def update_sentiment(db: Session, results: list, target_gall: str):
    for item in results:
        word = db.query(models.Word).filter(models.Word.id == item["word_id"])\
        .filter(models.Word.gallId == target_gall).first()
        if word:
            word.sentiment = item["final_score"]
            word.state = models.ProcessState.COMPLETED
    db.commit()
    

'''
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
'''
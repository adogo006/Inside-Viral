from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from DB_manager import models
from sqlalchemy import text

# words는 딕셔너리 자료들의 리스트 
def word_list_save(db: Session, words: list):

    stmt = insert(models.Word).values(words)
    try:
        db.execute(stmt)
        db.commit()
        print('파일 저장 완료')
    except Exception as e:
        db.rollback()
        print(f"실패! {e}")

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
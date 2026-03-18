from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from DB_manager import models
from sqlalchemy import text

# words는 딕셔너리 자료들의 리스트 
# def word_list_save(db: Session, words: list):

#     stmt = insert(models.Word).values(words)
#     try:
#         db.execute(stmt)
#         db.commit()
#         print('파일 저장 완료')
#     except Exception as e:
#         db.rollback()
#         print(f"실패! {e}")

def save_in_database(db: Session, word_list: list):
    try:
        db.add_all([models.Word(**d) for d in word_list]) 
        db.commit() 
        print("데이터 저장 완료")
        return 0

    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
        return -1
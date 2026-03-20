from sqlalchemy.orm import Session
from DB_manager import models
from DB_manager.database import SessionLocal
from sqlalchemy.dialects.postgresql import insert

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
    stmt = insert(models.Word).values(word_list)
    upsert_stmt = stmt.on_conflict_do_nothing( index_elements= ['gallId', 'date', 'wordContent'] )
    try:
        db.execute(upsert_stmt)
        db.commit()
        print("데이터 저장 중!")
        return 0

    except Exception as e:
        db.rollback()
        print(f"save_in_weights: 오류 발생: {e}")
        return -1
    
def export_to_txt():
    db = SessionLocal()
    all_words = db.query(models.Word.wordContent).all()
    with open('db_content.txt', 'w', encoding='utf-8') as f:
            for row in all_words:
                content = row[0]
                if content:
                    # 줄바꿈 문자를 제거하거나 공백으로 치환 (한 줄이 게시글 하나가 되도록)
                    clean_content = content.replace('\n', ' ').replace('\r', '').strip()
                    f.write(clean_content + '\n')

    print("친구에게 보낼 파일 생성 완료!")
    db.close()
    return
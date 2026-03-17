#실행 파일 (FAST_API 및 단순실행)
from database import engine, SessionLocal
from datetime import datetime
import models, crud


def test_database():

    print('db 테이블을 생성합니다.')
    models.Base.metadata.create_all(bind = engine)
    db = SessionLocal()
    
    try:
        print('데이터를 넣는 중입니다.') 
        crud.create_word_entry(db, 'testGallery', datetime.now(), '안녕하세요. 테스트입니다.', 0.8)   

        print('데이터를 출력합니다.')
        print(crud.get_words(db))

    except Exception as e:
        print(f'db 데이터 입력 실패! error: {e}')

    finally:
        db.close()

if __name__ == '__main__':
    test_database()




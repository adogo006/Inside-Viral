from sqlalchemy.orm import Session
from DB_manager import models
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func

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
    
def delete_whitespace_word(db: Session):
    deleted_count = db.query(models.Word).filter(
        (func.trim(models.Word.wordContent) == '') | 
        (models.Word.wordContent == None)
    ).delete(synchronize_session=False)
    db.commit()
    print('공백 데이터 삭제완료!')

def export_to_txt(db: Session):
    all_words = db.query(models.Word.wordContent).all()
    with open('db_content.txt', 'w', encoding='utf-8') as f:
            for row in all_words:
                content = row[0]
                if content:
                    # 줄바꿈 문자를 제거하거나 공백으로 치환 (한 줄이 게시글 하나가 되도록)
                    clean_content = content.replace('\n', ' ').replace('\r', '').strip()
                    f.write(clean_content + '\n')

    print("친구에게 보낼 파일 생성 완료!")
    return

# DB에서 모든 문장을 리스트로 가져오는 함수
# KeywordExtractor에서 직접 호출하여 사용
def get_all_sentences(db: Session):
    """
    DB에 저장된 모든 단어/문장을 리스트로 반환
    - 공백 및 None 값은 필터링
    - 줄바꿈 문자는 공백으로 치환
    """
    all_words = db.query(models.Word.wordContent).filter(
        models.Word.wordContent.isnot(None),
        func.trim(models.Word.wordContent) != ''
    ).all()

    sentences = []
    for row in all_words:
        content = row[0]
        if content:
            clean_content = content.replace('\n', ' ').replace('\r', '').strip()
            if clean_content:
                sentences.append(clean_content)

    print(f"DB에서 {len(sentences)}개의 문장을 읽었습니다.")
    return sentences

# 특정 갤러리의 문장만 가져오는 함수
def get_sentences_by_gallid(db: Session, gall_id: str):
    """
    특정 갤러리(gall_id)의 모든 단어/문장을 리스트로 반환
    """
    all_words = db.query(models.Word.wordContent).filter(
        models.Word.gallId == gall_id,
        models.Word.wordContent.isnot(None),
        func.trim(models.Word.wordContent) != ''
    ).all()

    sentences = []
    for row in all_words:
        content = row[0]
        if content:
            clean_content = content.replace('\n', ' ').replace('\r', '').strip()
            if clean_content:
                sentences.append(clean_content)

    print(f"갤러리 '{gall_id}'에서 {len(sentences)}개의 문장을 읽었습니다.")
    return sentences

# 특정 기간 내의 문장을 가져오는 함수
def get_sentences_by_date(db: Session, gall_id: str = None, days: int = None):
    """
    특정 갤러리의 특정 기간 내 문장을 가져옴
    - gall_id: 갤러리 ID (None이면 전체 갤러리)
    - days: 최근 n일 이내 (None이면 전체)
    """
    query = db.query(models.Word.wordContent).filter(
        models.Word.wordContent.isnot(None),
        func.trim(models.Word.wordContent) != ''
    )

    if gall_id:
        query = query.filter(models.Word.gallId == gall_id)

    if days is not None:
        from datetime import datetime, timedelta
        dt = datetime.now() - timedelta(days=days)
        query = query.filter(models.Word.date >= dt)

    all_words = query.all()

    sentences = []
    for row in all_words:
        content = row[0]
        if content:
            clean_content = content.replace('\n', ' ').replace('\r', '').strip()
            if clean_content:
                sentences.append(clean_content)

    print(f"조건에 맞하는 {len(sentences)}개의 문장을 읽었습니다.")
    return sentences
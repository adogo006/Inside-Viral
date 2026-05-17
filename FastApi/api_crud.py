from sqlalchemy.orm import Session
from DB_manager import models
from sqlalchemy.dialects.postgresql import insert

from schemas import RequestLogUpsert


def api_create_request_log(db: Session, request_log: RequestLogUpsert):
    values = request_log.model_dump(exclude_none=True)
    stmt = insert(models.RequestLog).values(**values)
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements=["request_id"],
        set_={
            "gall_main_url": stmt.excluded.gall_main_url,
            "days": stmt.excluded.days,
            "days_ago": stmt.excluded.days_ago,
            "status": stmt.excluded.status,
            "error_message": stmt.excluded.error_message,
            "saved_rows": stmt.excluded.saved_rows,
            "finished_at": stmt.excluded.finished_at,
        },
    )
    try:
        db.execute(upsert_stmt)
        db.commit()
        print(f"크롤링 요청({request_log.request_id}) 저장 완료")
        return 0

    except Exception as e:
        db.rollback()
        print(f"크롤링 요청({request_log.request_id}) 저장 실패: {e}")
        return -1

def api_get_request_log(db: Session, request_id: str):
    return db.query(models.RequestLog).filter(models.RequestLog.request_id == request_id).first()

def api_update_request_log(db: Session, request_id: str, request_log: RequestLogUpsert):
    existing_log = db.query(models.RequestLog).filter(models.RequestLog.request_id == request_id).first()
    if existing_log:
        for key, value in request_log.model_dump(exclude_none=True, exclude= {"request_id"}).items():
            setattr(existing_log, key, value)
        try:
            db.commit()
            print(f"크롤링 요청({request_log.request_id}) 로그 업데이트 완료")
            return 0
        except Exception as e:
            db.rollback()
            print(f"크롤링 요청({request_log.request_id}) 로그 업데이트 실패: {e}")
            return -1
    else:
        print(f"크롤링 요청({request_log.request_id}) 로그를 찾을 수 없습니다.")
        return -1


# AverageSentimentForOneDay CRUD
def api_get_average_sentiments(db: Session, gall_id: str, days: int = 7):
    """특정 갤러리의 최근 N일치 평균 감정지수 조회"""
    from datetime import datetime, timedelta, timezone
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return db.query(models.AverageSentimentForOneDay).filter(
        models.AverageSentimentForOneDay.gall_id == gall_id,
        models.AverageSentimentForOneDay.date >= dt
    ).order_by(models.AverageSentimentForOneDay.date.asc()).all()

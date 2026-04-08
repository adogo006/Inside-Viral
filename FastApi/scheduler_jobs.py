from datetime import datetime, timedelta, timezone

from DB_manager.database import SessionLocal
from DB_manager.models import RequestLog, Word
from DB_manager.crud import compute_average_sentiment


def cleanup_not_finished_logs() -> None:
    """Delete not finished request logs"""
    db = SessionLocal()
    try:
        deleted_logs = (
            db.query(RequestLog)
            .filter(RequestLog.finished_at.isnot(None))
            .delete(synchronize_session=False)
        )

        db.commit()
        print(
            f"[SCHEDULER] cleanup_not_finished_logs completed"
            f"deleted_logs={deleted_logs}"
        )
    except Exception as exc:
        db.rollback()
        print(f"[SCHEDULER] cleanup_not_finished_logs failed: {exc}")
    finally:
        db.close()

def compute_average_sentiment_for_all_galls() -> None:
    """Compute average sentiment for all galls and store in the database"""
    db = SessionLocal()
    try:
        gall_ids = db.query(Word.gallId).distinct().all()
        for gall_id_tuple in gall_ids:
            gall_id = gall_id_tuple[0]
            compute_average_sentiment(db, gall_id, datetime.now(), period=1)
            print(f"[SCHEDULER] compute_average_sentiment_for_{gall_id} completed")
        print(f"[SCHEDULER] compute_average_sentiment_for_all_galls completed")
    except Exception as exc:
        print(f"[SCHEDULER] compute_average_sentiment_for_all_galls failed: {exc}")
    finally:
        db.close()
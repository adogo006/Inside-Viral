from datetime import datetime, timedelta, timezone

from DB_manager.database import SessionLocal
from DB_manager.models import RequestLog, Word


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

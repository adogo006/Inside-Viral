from datetime import datetime, timedelta, timezone
import os
import time

import httpx

from FastApi.main import request_api_crawling, cancel_api_crawling
from DB_manager.database import SessionLocal
from DB_manager.models import RequestLog, Word, RequestStatus
from DB_manager.crud import compute_average_sentiment, delete_low_priority_words, get_request_status


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

def compute_average_sentiment_in_scheduler() -> None:
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

def delete_low_priority_words_in_scheduler() -> None:
    """Delete low priority words from the database"""
    db = SessionLocal()
    try:
        deleted_count = delete_low_priority_words(db, threshold=1000)    
        print(f"[SCHEDULER] delete_low_priority_words completed, deleted_count={deleted_count}")
    except Exception as exc:
        db.rollback()
        print(f"[SCHEDULER] delete_low_priority_words failed: {exc}")
    finally:
        db.close()

def request_crawlling_in_scheduler() -> None:
    """Request previous-day crawling for all galls and retry on failed/cancelled."""
    retry_limit = int(os.getenv("SCHEDULER_CRAWL_RETRY_LIMIT", "2"))
    timeout_sec = int(os.getenv("SCHEDULER_CRAWL_TIMEOUT_SEC", "1800"))
    poll_interval_sec = float(os.getenv("SCHEDULER_CRAWL_POLL_INTERVAL_SEC", "5"))

    dict_urls_request_id = {
        "https://gall.dcinside.com/mgallery/board/lists/?id=stockus" : None,
        "https://gall.dcinside.com/mgallery/board/lists/?id=krstock" : None,
        "https://gall.dcinside.com/board/lists/?id=bitcoins_new1" : None,
        "https://gall.dcinside.com/mgallery/board/lists/?id=tenbagger" : None,
    }

    success_count = 0

    for gall_main_url in dict_urls_request_id.keys():
        payload = {
            "gall_main_url": gall_main_url,
            "days": 1,
            "days_ago": 1,
        }
        response = request_api_crawling(payload)
        dict_urls_request_id[gall_main_url] = response["request_id"]

    end_time = time.monotonic() + timeout_sec
    end_count = len(dict_urls_request_id)

    while success_count < end_count and time.monotonic() < end_time:
        time.sleep(poll_interval_sec)
        for gall_main_url, request_id in dict_urls_request_id.items():
            db = SessionLocal()
            try:
                status = get_request_status(db, request_id)
            except Exception as exc:
                db.rollback()
                print(f"[SCHEDULER] 요청에 대한 상태를 가져오는데 실패했습니다. request_id={request_id}, error={exc}")
                status = None
            finally:                
                db.close()

            if request_id in {None, RequestStatus.SUCCEEDED.value, RequestStatus.FAILED.value, RequestStatus.CANCELLED.value, RequestStatus.DISPATCH_FAILED.value}:
                payload = {
                    "gall_main_url": gall_main_url,
                    "days": 1,
                    "days_ago": 1,
                }
                response = request_api_crawling(payload)
                dict_urls_request_id[gall_main_url] = response["request_id"]
                continue

            if status == RequestStatus.SUCCEEDED.value:
                print(f"[SCHEDULER] Crawling succeeded for {gall_main_url} (request_id={request_id})")
                dict_urls_request_id.pop(gall_main_url, None)
                success_count += 1

    if success_count == end_count:
        print(f"[SCHEDULER] All crawling tasks completed successfully within the timeout.")
    else:
        print(f"[SCHEDULER] Crawling tasks did not complete within the timeout.")
        for gall_main_url, request_id in dict_urls_request_id.items():
            cancel_api_crawling(request_id)
            print(f" - Failed: {gall_main_url} (request_id={request_id})")

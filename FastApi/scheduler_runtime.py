import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduler_jobs import cleanup_not_finished_logs

_scheduler: AsyncIOScheduler | None = None


def _build_cron_trigger(expr: str) -> CronTrigger:
    """Convert a 5-field cron string to APScheduler CronTrigger."""
    fields = expr.split()
    if len(fields) != 5:
        raise ValueError("DB_CLEANUP_CRON must have 5 fields: m h dom mon dow")

    minute, hour, day, month, day_of_week = fields
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        timezone="UTC",
    )


def start_scheduler() -> None:
    global _scheduler

    enabled = os.getenv("ENABLE_CLEANUP_SCHEDULER", "true").lower() == "true"
    if not enabled:
        print("[SCHEDULER] disabled by ENABLE_CLEANUP_SCHEDULER")
        return

    if _scheduler is not None and _scheduler.running:
        return

    retention_days = int(os.getenv("DB_CLEANUP_RETENTION_DAYS", "7"))
    cron_expr = os.getenv("DB_CLEANUP_CRON", "0 4 * * *")

    try:
        trigger = _build_cron_trigger(cron_expr)
    except ValueError as exc:
        print(f"[SCHEDULER] invalid DB_CLEANUP_CRON '{cron_expr}': {exc}. fallback to 0 4 * * *")
        trigger = _build_cron_trigger("0 4 * * *")

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        cleanup_not_finished_logs,
        trigger=trigger,
        id="db_cleanup_logs",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        # kwargs={"retention_days": retention_days},
    )
    _scheduler.start()

    print(
        f"[SCHEDULER] started: cron='{cron_expr}' UTC, retention_days={retention_days}"
    )


def stop_scheduler() -> None:
    global _scheduler

    if _scheduler is None:
        return

    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[SCHEDULER] stopped")

    _scheduler = None

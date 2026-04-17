import logging
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from services.url_safety import validate_safe_url, UnsafeUrlError
from .core import get_scraper

logger = logging.getLogger("priceradar.scraper")

async def scrape_competitor_url(db: Session, comp_url: models.CompetitorUrl):
    # Defence in depth: URLs are validated on write, but legacy rows or
    # a later DNS rebind could still point somewhere unsafe. Re-check here.
    try:
        validate_safe_url(comp_url.url)
    except UnsafeUrlError as e:
        logger.warning(
            "Refusing to scrape unsafe URL (id=%s): %s — %s",
            comp_url.id, comp_url.url, e,
        )
        return False

    scraper = get_scraper(comp_url.url)
    price, stock = await scraper.scrape(comp_url.url)

    if price is not None:
        new_history = models.PriceHistory(
            competitor_url_id=comp_url.id,
            price=price,
            stock_status=stock,
            scraped_at=datetime.now(timezone.utc)
        )
        db.add(new_history)
        db.commit()
        logger.info(f"Successfully scraped {comp_url.url}: ¥{price} ({stock})")

        # Trigger LINE notifications (price loss / recovery / stock out / stock in).
        # 通知失敗はスクレイプ成功を巻き込まない。exc_info でスタックトレースも残す。
        try:
            from services.notifications import check_and_notify_price_event
            await check_and_notify_price_event(db, comp_url, price, stock)
        except Exception:
            logger.exception(
                "Notification check failed for comp_url_id=%s url=%s",
                comp_url.id, comp_url.url,
            )

        return True
    else:
        logger.warning(f"Failed to extract price from {comp_url.url}")
        return False

# Per-URL failure tracker for the scheduled job. Three consecutive failures
# put a URL in "penalty" for PENALTY_SECONDS so we don't hammer a broken
# target every hour. Reset on the first success. In-memory only; on restart
# everything is retried once.
_FAILURE_COUNTS: dict[int, int] = {}
_PENALTY_UNTIL: dict[int, float] = {}
_FAILURE_THRESHOLD = 3
_PENALTY_SECONDS = 60 * 60 * 6  # 6 hours


def _record_scrape_result(url_id: int, ok: bool) -> None:
    import time
    if ok:
        _FAILURE_COUNTS.pop(url_id, None)
        _PENALTY_UNTIL.pop(url_id, None)
        return
    count = _FAILURE_COUNTS.get(url_id, 0) + 1
    _FAILURE_COUNTS[url_id] = count
    if count >= _FAILURE_THRESHOLD:
        _PENALTY_UNTIL[url_id] = time.time() + _PENALTY_SECONDS
        logger.warning(
            "URL id=%s reached %s consecutive failures — skipping scheduled scrapes for %sh",
            url_id, count, _PENALTY_SECONDS // 3600,
        )


def _in_penalty(url_id: int) -> bool:
    import time
    until = _PENALTY_UNTIL.get(url_id)
    if until is None:
        return False
    if time.time() >= until:
        _PENALTY_UNTIL.pop(url_id, None)
        _FAILURE_COUNTS.pop(url_id, None)
        return False
    return True


async def run_scheduled_scraping():
    db = SessionLocal()
    try:
        # Get all active competitor URLs
        comp_urls = db.query(models.CompetitorUrl).join(models.Product).filter(models.Product.is_active == True).all()
        eligible = [c for c in comp_urls if not _in_penalty(c.id)]
        skipped = len(comp_urls) - len(eligible)
        if skipped:
            logger.info(f"Skipping {skipped} URLs currently in failure-penalty window")
        logger.info(f"Starting scheduled scraping job for {len(eligible)} URLs")

        # In a real SaaS, we'd distribute these or batch them
        # For this PoC, we run concurrently but with a limit
        concurrency = 2
        semaphore = asyncio.Semaphore(concurrency)

        async def scrape_with_sema(url_obj):
            async with semaphore:
                ok = await scrape_competitor_url(db, url_obj)
                _record_scrape_result(url_obj.id, bool(ok))

        tasks = [scrape_with_sema(c) for c in eligible]
        if tasks:
            await asyncio.gather(*tasks)

        logger.info("Scheduled scraping job completed")
    finally:
        db.close()


async def cleanup_old_history():
    """Delete price history older than the per-plan retention window.

    Iterates every plan in PLAN_LIMITS and honours retention_days per plan.
    Plans with retention_days=None (Pro, Enterprise) are skipped entirely.
    Defensive: we refuse to delete anything unless retention_days is a
    positive int, so a misconfigured plan can never wipe all history.
    """
    db = SessionLocal()
    try:
        total_deleted = 0
        for plan_key, plan_config in models.PLAN_LIMITS.items():
            retention = plan_config.get("history_retention_days")
            if not isinstance(retention, int) or retention <= 0:
                continue

            user_ids = [
                uid for (uid,) in db.query(models.User.id)
                .filter(models.User.plan == plan_key).all()
            ]
            if not user_ids:
                continue

            cutoff = datetime.now(timezone.utc) - timedelta(days=retention)
            deleted = db.query(models.PriceHistory)\
                .filter(
                    models.PriceHistory.scraped_at < cutoff,
                    models.PriceHistory.competitor_url_id.in_(
                        db.query(models.CompetitorUrl.id).join(models.Product).filter(
                            models.Product.user_id.in_(user_ids)
                        )
                    )
                ).delete(synchronize_session=False)
            db.commit()
            if deleted:
                logger.info(f"Cleaned up {deleted} old price history records for plan={plan_key}")
                total_deleted += deleted

        # Also cap NotificationLog retention (kept for 90 days regardless of plan).
        notif_cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        notif_deleted = db.query(models.NotificationLog)\
            .filter(models.NotificationLog.sent_at < notif_cutoff)\
            .delete(synchronize_session=False)
        db.commit()
        if notif_deleted:
            logger.info(f"Cleaned up {notif_deleted} old notification log rows")
    except Exception as e:
        logger.error(f"History cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()

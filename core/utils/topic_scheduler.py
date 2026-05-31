"""
APScheduler 기반 토픽 자동 교체 스케줄러.

매일 자정(KST)에 rotate_topic() 을 실행하여
어제 토픽을 비활성화하고, 오늘 날짜의 토픽을 활성화합니다.
"""

import logging
from datetime import date

logger = logging.getLogger('core.scheduler')


def rotate_topic():
    """
    1. 현재 활성 토픽(is_active=True) 비활성화
    2. 오늘 publish_date 인 토픽 활성화
    """
    from core.models.topic import Topic

    today = date.today()
    logger.info("rotate_topic started: today=%s", today)

    # 기존 활성 토픽 비활성화
    deactivated = Topic.objects.filter(is_active=True).update(is_active=False)
    if deactivated:
        logger.info("Deactivated %d topic(s)", deactivated)

    # 오늘 날짜 토픽 활성화
    activated = Topic.objects.filter(
        publish_date=today, is_active=False
    ).update(is_active=True)

    if activated:
        logger.info("Activated %d topic(s) for %s", activated, today)
    else:
        logger.warning("No topic found for today (%s)", today)


def start_scheduler():
    """APScheduler BackgroundScheduler 를 시작합니다."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.error(
            "APScheduler is not installed. "
            "Run: pip install APScheduler>=3.10.0"
        )
        return

    scheduler = BackgroundScheduler(timezone='Asia/Seoul')
    scheduler.add_job(
        rotate_topic,
        trigger=CronTrigger(hour=0, minute=0, timezone='Asia/Seoul'),
        id='rotate_topic',
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Topic rotation scheduler started (daily 00:00 KST)")

    # 서버 시작 시 오늘 토픽도 즉시 활성화 시도
    rotate_topic()

"""
In-memory token-bucket rate limiter (thread-safe).

Prevents rapid-fire actions like comment/like/vote spam.
"""

import time
import threading
import logging

logger = logging.getLogger('core.security')


class RateLimiter:
    """
    간단한 인-메모리 rate limiter.

    LIMITS 딕셔너리의 키(action)마다 최소 대기 시간(초)을 지정합니다.
    같은 student_id + action 조합이 대기 시간 이내에 다시 요청하면 차단합니다.
    """

    # action → 최소 간격(초)
    LIMITS: dict[str, float] = {
        'comment': 5.0,
        'like': 0.5,
        'vote': 1.0,
    }

    def __init__(self) -> None:
        # key: (student_id, action) → last_request_time
        self._records: dict[tuple[int, str], float] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, student_id: int, action: str) -> bool:
        """
        Returns True  → 요청 허용 (통과)
        Returns False → rate-limited (차단)
        """
        interval = self.LIMITS.get(action)
        if interval is None:
            return True  # 정의되지 않은 action은 제한 없음

        key = (student_id, action)
        now = time.time()

        with self._lock:
            last = self._records.get(key, 0.0)
            if now - last < interval:
                logger.warning(
                    "Rate limited: student_id=%s action=%s elapsed=%.1fs limit=%ds",
                    student_id, action, now - last, interval,
                )
                return False
            self._records[key] = now
            return True


# Singleton instance
rate_limiter = RateLimiter()

# in-mem or Redis rate limiter

import time
from collections import defaultdict, deque
from typing import Deque


class RateLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self._hits: dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        window = now - 60
        dq = self._hits[key]
        while dq and dq[0] < window:
            dq.popleft()
        if len(dq) >= self.per_minute:
            return False
        dq.append(now)
        return True

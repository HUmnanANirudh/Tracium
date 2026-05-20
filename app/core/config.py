from collections import defaultdict
from time import time
import threading
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    max_payload_bytes: int = 1_048_576
    max_logs_per_request: int = 1000
    max_requests_per_minute: int = 60
    max_logs_per_minute: int = 5000


class RateLimiter:
    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.log_counts: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._lock = threading.Lock()

    def _clean_old(self, bucket: list, window: int):
        now = time()
        bucket[:] = [t for t in bucket if now - t < window]

    def check(self, client_id: str, log_count: int, config: RateLimitConfig) -> tuple[bool, str]:
        now = time()
        window = 60

        with self._lock:
            self._clean_old(self.requests[client_id], window)
            self.log_counts[client_id][:] = [
                (t, c) for t, c in self.log_counts[client_id] if now - t < window
            ]

            total_logs = sum(c for _, c in self.log_counts[client_id])

            if len(self.requests[client_id]) >= config.max_requests_per_minute:
                return False, f"Rate limit: max {config.max_requests_per_minute} requests per {window}s"

            if total_logs + log_count > config.max_logs_per_minute:
                return False, f"Rate limit: max {config.max_logs_per_minute} logs per {window}s"

            self.requests[client_id].append(now)
            self.log_counts[client_id].append((now, log_count))

        return True, ""


config = RateLimitConfig()
limiter = RateLimiter()
limiter_check = limiter.check
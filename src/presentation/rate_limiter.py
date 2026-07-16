import time
from collections import defaultdict
from typing import Optional

from sanic import Sanic
from sanic.request import Request

from src.application.errors import ApplicationError


class RateLimitExceededError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Rate limit exceeded. Try again later.", status_code=429)


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter keyed by (route, client_key).

    Tracks request timestamps per window; drops expired entries on each check.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._buckets: dict[tuple[str, str], list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        """Derive a client identifier from the request.

        Prefers X-Forwarded-For over remote IP for reverse-proxy deployments.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.ip or "unknown"

    def check(self, request: Request) -> None:
        route = request.path
        key = self._client_key(request)
        now = time.monotonic()
        window_start = now - self._window_seconds
        bucket_key = (route, key)

        timestamps = self._buckets[bucket_key]
        # Drop expired entries
        while timestamps and timestamps[0] < window_start:
            timestamps.pop(0)

        if len(timestamps) >= self._max_requests:
            raise RateLimitExceededError()

        timestamps.append(now)


def setup_rate_limiter(
    app: Sanic,
    limits: Optional[list[tuple[str, str, int, float]]] = None,
) -> SlidingWindowRateLimiter:
    """Register rate-limit middleware.

    `limits` — list of (method, path_prefix, max_requests, window_seconds).
    Default: 10 requests / 60 s on POST /payments/webhook.
    """
    if limits is None:
        limits = [("POST", "/payments/webhook", 10, 60.0)]

    limiter = SlidingWindowRateLimiter(max_requests=0, window_seconds=1.0)

    # Store limits as a list of rules on the limiter itself for the middleware
    rule_set: list[tuple[str, str, int, float]] = list(limits)

    @app.middleware("request")
    async def rate_limit_middleware(request: Request):
        for method, prefix, max_r, window_s in rule_set:
            if request.method == method and request.path.startswith(prefix):
                # Temporarily reconfigure the limiter for this check
                limiter._max_requests = max_r
                limiter._window_seconds = window_s
                limiter.check(request)
                break

    return limiter

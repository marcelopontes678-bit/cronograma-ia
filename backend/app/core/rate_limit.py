import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Limitador de taxa em memória (janela deslizante, por processo).

    Suficiente para uma instância única; em produção com múltiplas
    réplicas, trocar por um backend compartilhado (Redis).
    """

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.max_attempts:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas. Aguarde um instante e tente novamente.",
            )
        hits.append(now)

    def reset(self) -> None:
        self._hits.clear()


login_limiter = RateLimiter(max_attempts=5, window_seconds=60)
refresh_limiter = RateLimiter(max_attempts=10, window_seconds=60)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit_login(request: Request) -> None:
    login_limiter.check(_client_key(request))


def rate_limit_refresh(request: Request) -> None:
    refresh_limiter.check(_client_key(request))

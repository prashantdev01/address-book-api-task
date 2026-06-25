import structlog
from cachetools import TTLCache
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

# Cache up to 10,000 keys, each valid for 24 hours
_idempotency_cache: TTLCache = TTLCache(maxsize=10_000, ttl=86_400)

IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Prevents duplicate processing of the same request.

    Clients must send an `Idempotency-Key` header (e.g. a UUID) with mutating
    requests. If the same key is seen again within 24 hours, the original
    cached response is returned without re-executing the handler.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in IDEMPOTENT_METHODS:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        if idempotency_key in _idempotency_cache:
            cached = _idempotency_cache[idempotency_key]
            logger.info(
                "idempotency_cache_hit",
                key=idempotency_key,
                path=request.url.path,
            )
            return Response(
                content=cached["body"],
                status_code=cached["status_code"],
                media_type="application/json",
                headers={"X-Idempotency-Replayed": "true"},
            )

        response = await call_next(request)

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Only cache successful responses — don't cache 4xx/5xx
        if response.status_code < 400:
            _idempotency_cache[idempotency_key] = {
                "body": body,
                "status_code": response.status_code,
            }
            logger.info(
                "idempotency_key_stored",
                key=idempotency_key,
                path=request.url.path,
                status_code=response.status_code,
            )

        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type="application/json",
        )

"""Auth + request-tracking middlewares.

- ``InternalAuthorization``: API-key gate. Canonical header is
  ``x-api-key``; the legacy ``api-key`` header is still accepted.
- ``TrackingHeadersMiddleware``: reads ``user_id`` / ``generation_id``
  from the JSON request body (when present), stores them on
  ``request.state``, and echoes them back as ``X-User-Id`` /
  ``X-Generation-Id`` response headers for tracing.
"""

import json
import logging
import os
import secrets
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, Header, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.lib.constants import HEADER_GENERATION_ID, HEADER_USER_ID

load_dotenv()

logger = logging.getLogger(__name__)


def _expected_api_key() -> str:
    key = os.getenv("API_KEY")
    if not key:
        logger.error("API_KEY is not configured")
        raise HTTPException(status_code=500, detail="Server misconfigured: API_KEY missing")
    return key


def InternalAuthorization(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="x-api-key"),
    api_key_legacy: Optional[str] = Header(default=None, alias="api-key"),
):
    provided = x_api_key if x_api_key is not None else api_key_legacy
    if not provided:
        raise HTTPException(status_code=401, detail="Missing API key")
    expected = _expected_api_key()
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid Api Key")
    return True


class TrackingHeadersMiddleware(BaseHTTPMiddleware):
    """Echo user_id / generation_id from JSON body into response headers.

    Body is read once and replayed so downstream handlers still see it.
    Non-JSON or key-less bodies are passed through untouched.
    """

    async def dispatch(self, request: Request, call_next):
        user_id: Optional[str] = None
        generation_id: Optional[str] = None
        try:
            body = await request.body()
            if body:
                try:
                    payload = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    payload = None
                if isinstance(payload, dict):
                    raw_user = payload.get("user_id")
                    raw_gen = payload.get("generation_id")
                    user_id = str(raw_user) if raw_user is not None else None
                    generation_id = str(raw_gen) if raw_gen is not None else None

                # Replay the consumed body for downstream handlers.
                async def _receive():
                    return {"type": "http.request", "body": body, "more_body": False}

                request._receive = _receive  # type: ignore[attr-defined]
        except Exception as exc:  # never break the request on tracking
            logger.debug("tracking middleware body read failed: %s", exc)

        request.state.user_id = user_id
        request.state.generation_id = generation_id

        response: Response = await call_next(request)
        if user_id:
            response.headers[HEADER_USER_ID] = user_id
        if generation_id:
            response.headers[HEADER_GENERATION_ID] = generation_id
        return response


__all__ = ["InternalAuthorization", "TrackingHeadersMiddleware"]

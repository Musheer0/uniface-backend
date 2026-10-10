"""Shared router helpers: error mapping + safe temp cleanup."""

import logging
import os
import subprocess

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def cleanup_paths(*paths: str) -> None:
    for path in paths:
        if not path:
            continue
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError as exc:
            logger.warning("cleanup failed for %s: %s", path, exc)


def to_http_exception(exc: Exception, generation_id: str = "") -> HTTPException:
    prefix = f"[generation_id={generation_id}] " if generation_id else ""
    if isinstance(exc, HTTPException):
        return exc
    if isinstance(exc, FileNotFoundError):
        logger.warning("%snot found: %s", prefix, exc)
        return HTTPException(status_code=404, detail=str(exc))
    msg = str(exc)
    lowered = msg.lower()
    if "no face found" in lowered or "no face" in lowered:
        logger.info("%s%s", prefix, msg)
        return HTTPException(status_code=422, detail=msg)
    if isinstance(exc, (ValueError, IOError, OSError)):
        logger.warning("%sbad request/processing error: %s", prefix, exc)
        # Distinguish client errors (bad media/keys) from server I/O faults
        # by message convention: unreadable inputs -> 400, write faults -> 500.
        if isinstance(exc, ValueError):
            return HTTPException(status_code=400, detail=msg)
        return HTTPException(status_code=500, detail=msg)
    if isinstance(exc, subprocess.CalledProcessError):
        logger.error("%sffmpeg failed: %s", prefix, exc)
        return HTTPException(status_code=500, detail="Video encoding failed")
    logger.exception("%sunexpected error", prefix)
    return HTTPException(status_code=500, detail="Internal processing error")


__all__ = ["cleanup_paths", "to_http_exception"]

"""Operational endpoints (no auth): liveness + model/storage readiness."""

import logging
import os

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ops"])


@router.get("/healthz")
def healthz():
    return {"ok": True}


@router.get("/readyz")
def readyz():
    """Warm cached models and check S3 bucket reachability (best effort)."""
    from src.lib.get_detector import warmup

    models = warmup()
    s3_ok: bool | None = None
    s3_error: str | None = None
    try:
        from src.lib.s3 import bucket, s3

        if not bucket:
            s3_ok = False
            s3_error = "S3_BUCKET not configured"
        else:
            s3.head_bucket(Bucket=bucket)
            s3_ok = True
    except Exception as exc:  # noqa: BLE001 - readiness probe, report only
        s3_ok = False
        s3_error = str(exc)[:300]
    return {
        "ok": s3_ok is not False,
        "models": models,
        "s3_ok": s3_ok,
        "s3_error": s3_error,
        "temp_dir": os.path.abspath(os.getenv("TEMP_DIR", "temp")),
    }

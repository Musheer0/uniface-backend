"""Shared request field types (single source of truth for key validation)."""

from typing import Annotated

from pydantic import AfterValidator

from src.lib.paths import safe_join  # noqa: F401  (re-export for convenience)


def _validate_s3_key(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("file key must not be empty")
    normalized = value.replace("\\", "/").strip()
    if normalized.startswith("/"):
        raise ValueError("absolute file keys are not allowed")
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise ValueError("invalid file key (path traversal)")
    return normalized


S3Key = Annotated[str, AfterValidator(_validate_s3_key)]

__all__ = ["S3Key"]

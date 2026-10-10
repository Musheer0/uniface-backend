"""Path helpers: keep S3 keys sandboxed inside the per-job temp dirs."""

import os

__all__ = ["safe_join", "ensure_parent"]


def safe_join(base_dir: str, key: str) -> str:
    """Join an S3-style ``key`` onto ``base_dir`` and reject escapes.

    Rejects empty keys, absolute paths and any ``..`` segment (POSIX and
    Windows separators). Returns the absolute destination path, guaranteed
    to stay inside ``base_dir``.
    """
    if not key or not key.strip():
        raise ValueError("file key must not be empty")
    normalized = key.replace("\\", "/").strip()
    if normalized.startswith("/"):
        raise ValueError(f"absolute file keys are not allowed: {key!r}")
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise ValueError(f"invalid file key (path traversal): {key!r}")

    base_abs = os.path.abspath(base_dir)
    dest = os.path.abspath(os.path.join(base_abs, *parts))
    if dest != base_abs and not dest.startswith(base_abs + os.sep):
        raise ValueError(f"invalid file key (escapes base dir): {key!r}")
    return dest


def ensure_parent(path: str) -> str:
    """Create the parent directory of ``path`` and return ``path``."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path

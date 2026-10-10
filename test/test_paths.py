"""S3-key sandboxing: traversal / absolute / empty keys are rejected."""

import os

import pytest

from src.lib.paths import ensure_parent, safe_join
from src.schemas.common import S3Key
from pydantic import BaseModel, ValidationError


class M(BaseModel):
    key: S3Key


def test_safe_join_ok(tmp_path):
    dest = safe_join(str(tmp_path), "inputs/photo.jpg")
    assert dest == os.path.join(str(tmp_path), "inputs", "photo.jpg")


def test_safe_join_rejects_traversal(tmp_path):
    for bad in ("../etc/passwd", "a/../../b", "..", "a/../.."):
        with pytest.raises(ValueError):
            safe_join(str(tmp_path), bad)


def test_safe_join_rejects_absolute_and_empty(tmp_path):
    with pytest.raises(ValueError):
        safe_join(str(tmp_path), "/abs/path.jpg")
    with pytest.raises(ValueError):
        safe_join(str(tmp_path), "")
    with pytest.raises(ValueError):
        safe_join(str(tmp_path), "   ")


def test_safe_join_rejects_dotdot_anywhere(tmp_path):
    # '..' is rejected even when the resolved path would stay inside the base
    with pytest.raises(ValueError):
        safe_join(str(tmp_path), "a/b/../c.jpg")


def test_s3key_validator():
    M(key="inputs/a.jpg")
    with pytest.raises(ValidationError):
        M(key="../../etc/x")
    with pytest.raises(ValidationError):
        M(key="/abs.jpg")


def test_ensure_parent_creates(tmp_path):
    target = os.path.join(str(tmp_path), "sub", "dir", "f.jpg")
    assert ensure_parent(target) == target
    assert os.path.isdir(os.path.dirname(target))

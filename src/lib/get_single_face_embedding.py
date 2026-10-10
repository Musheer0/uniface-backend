"""Reference-face embeddings with a content-hash cache.

``get_single_face_embedding`` takes a *local* reference-face image path
(downloaded from ``face_key`` by the routers) and returns its normalized
ArcFace embedding. Results are cached by SHA-256 of the file bytes so the
same reference image is encoded only once per container.
"""

import hashlib
import logging
import os
from typing import Any

import cv2

from src.lib.get_detector import get_detector, get_recognizer

logger = logging.getLogger(__name__)

_embedding_cache: dict[str, Any] = {}


def _file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create_face_embedding(face_img_path: str, detector=None) -> Any:
    face_image = cv2.imread(face_img_path)
    if face_image is None:
        raise ValueError(f"Could not read reference face image: {face_img_path}")
    detector = detector or get_detector()
    faces = detector.detect(face_image)
    if not faces:
        raise ValueError("No face found in reference image")
    if len(faces) > 1:
        logger.warning(
            "Reference image %s contains %d faces; using the first",
            face_img_path,
            len(faces),
        )
    recognizer = get_recognizer()
    return recognizer.get_normalized_embedding(face_image, faces[0].landmarks)


def get_single_face_embedding(faceId: str = "", face_id: str = "") -> Any:
    """Return the embedding for a local reference-face image.

    Accepts both ``faceId`` (legacy camelCase used by video libs) and
    ``face_id``. Results are cached by file content hash.
    """
    face_path = face_id or faceId
    if not face_path:
        raise ValueError("face_id is required")
    if not os.path.exists(face_path):
        raise FileNotFoundError(f"Reference face file not found: {face_path}")

    key = _file_sha256(face_path)
    cached = _embedding_cache.get(key)
    if cached is not None:
        return cached

    embedding = create_face_embedding(face_path, get_detector())
    _embedding_cache[key] = embedding
    return embedding


def clear_embedding_cache() -> None:
    _embedding_cache.clear()


__all__ = [
    "create_face_embedding",
    "get_single_face_embedding",
    "clear_embedding_cache",
]

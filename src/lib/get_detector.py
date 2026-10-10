"""Cached model factories.

RetinaFace / ArcFace load ONNX weights on construction, which costs seconds
per request when built fresh. These helpers memoize one instance per process
so warm Modal containers reuse them. Call ``warmup()`` at startup (healthz)
to pay the cost once and to log which onnxruntime providers are active.
"""

import functools
import logging

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_detector():
    from uniface.detection import RetinaFace

    detector = RetinaFace()
    logger.info("RetinaFace detector initialized (cached)")
    return detector


@functools.lru_cache(maxsize=1)
def get_recognizer():
    from uniface.recognition import ArcFace

    recognizer = ArcFace()
    logger.info("ArcFace recognizer initialized (cached)")
    return recognizer


def warmup() -> dict:
    """Eagerly build cached models and report onnxruntime providers."""
    detector = get_detector()
    recognizer = get_recognizer()
    providers: list[str] = []
    try:
        import onnxruntime as ort

        providers = ort.get_available_providers()
        logger.info("onnxruntime providers: %s", providers)
    except Exception:  # pragma: no cover - optional dependency introspection
        logger.info("onnxruntime provider list unavailable")
    return {
        "detector": type(detector).__name__,
        "recognizer": type(recognizer).__name__,
        "providers": providers,
    }


__all__ = ["get_detector", "get_recognizer", "warmup"]

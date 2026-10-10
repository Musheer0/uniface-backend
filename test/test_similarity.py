"""Shared similarity threshold + filtered-frame selection direction.

Convention: lower distance => same person. Filtered paths blur faces with
distance <= SIMILARITY_THRESHOLD (different people) and keep the reference
person clear.
"""

from types import SimpleNamespace

import src.lib.blur_video as blur_video_mod
import src.lib.blur_video_with_timestamps as ts_mod
from src.lib.constants import SIMILARITY_THRESHOLD


def test_single_shared_threshold():
    assert SIMILARITY_THRESHOLD == 0.3
    assert blur_video_mod.SIMILARITY_THRESHOLD == SIMILARITY_THRESHOLD
    # timestamp module must not define its own divergent threshold
    assert not hasattr(ts_mod, "SIMILARITY_THRESHOLD")


def test_process_frame_filtered_direction(monkeypatch):
    calls = {}

    same = SimpleNamespace(landmarks="same")
    other = SimpleNamespace(landmarks="other")

    class Detector:
        def detect(self, frame):
            return [same, other]

    class Recognizer:
        def get_normalized_embedding(self, frame, landmarks):
            return f"emb-{landmarks}"

    class Blurrer:
        def anonymize(self, frame, faces):
            calls["faces"] = list(faces)
            return frame

    def fake_similarity(emb1=None, emb2=None, **kw):
        # target "ref" matches "same" (high distance value), differs from other
        return 0.9 if emb2 == "emb-same" else 0.1

    monkeypatch.setattr(blur_video_mod, "compute_similarity", fake_similarity)

    out = blur_video_mod.process_frame_filtered(
        "frame", Detector(), Recognizer(), Blurrer(), target_face="ref"
    )
    assert out == "frame"
    # only the non-matching face is blurred
    assert calls["faces"] == [other]

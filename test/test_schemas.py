"""Schema validation: keys, blur methods, timestamp ranges."""

import pytest
from pydantic import ValidationError

from src.schemas.blur_photo_schemas import (
    BlurEveryoneFilteredRequest as PhotoFiltered,
)
from src.schemas.blur_photo_schemas import BlurEveryoneRequest as PhotoReq
from src.schemas.blur_video_schemas import BlurEveryoneRequest as VideoReq
from src.schemas.blur_video_timestamp_schemas import (
    BlurEveryoneFilteredRequest as TsFiltered,
)
from src.schemas.blur_video_timestamp_schemas import BlurEveryoneRequest as TsReq


def _photo(**kw):
    base = {
        "user_id": "u1",
        "generation_id": "g1",
        "img_key": "inputs/a.jpg",
        "blur_method": "pixelate",
        "output_key": "outputs/a.jpg",
    }
    base.update(kw)
    return PhotoReq(**base)


def test_photo_ok_and_bad_method():
    _photo()
    with pytest.raises(ValidationError):
        _photo(blur_method="laser")


def test_photo_rejects_traversal():
    with pytest.raises(ValidationError):
        _photo(img_key="../evil.jpg")
    with pytest.raises(ValidationError):
        _photo(output_key="/abs.jpg")


def test_photo_filtered_requires_face_key():
    with pytest.raises(ValidationError):
        PhotoFiltered(
            user_id="u1", generation_id="g1", img_key="i.jpg",
            blur_method="gaussian", output_key="o.jpg",
        )


def test_video_keys():
    VideoReq(
        user_id="u", generation_id="g", video_key="inputs/v.mp4",
        blur_method="blackout", output_key="outputs/v.mp4",
    )
    with pytest.raises(ValidationError):
        VideoReq(
            user_id="u", generation_id="g", video_key="../v.mp4",
            blur_method="blackout", output_key="outputs/v.mp4",
        )


def _ts(**kw):
    base = {
        "user_id": "u1",
        "generation_id": "g1",
        "video_key": "inputs/v.mp4",
        "blur_method": "median",
        "output_key": "outputs/v.mp4",
        "timestamp_ranges": [(1.0, 2.0)],
    }
    base.update(kw)
    return TsReq(**base)


def test_timestamp_ranges_ok():
    _ts(timestamp_ranges=[[0, 1.5], [2.5, 6.0]])


def test_timestamp_start_after_end_rejected():
    with pytest.raises(ValidationError):
        _ts(timestamp_ranges=[[5.0, 2.0]])


def test_timestamp_negative_rejected():
    with pytest.raises(ValidationError):
        _ts(timestamp_ranges=[[-1.0, 2.0]])


def test_timestamp_too_many_rejected():
    with pytest.raises(ValidationError):
        _ts(timestamp_ranges=[(0.0, 1.0)] * 33)


def test_timestamp_filtered_needs_face():
    with pytest.raises(ValidationError):
        TsFiltered(
            user_id="u", generation_id="g", video_key="v.mp4",
            blur_method="pixelate", output_key="o.mp4",
            timestamp_ranges=[(0.0, 1.0)],
        )

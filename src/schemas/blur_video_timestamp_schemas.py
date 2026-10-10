from pydantic import field_validator

from src.lib.constants import MAX_TIMESTAMP_RANGES, MAX_TIMESTAMP_SECONDS
from src.schemas.base_schema import BaseRequest
from src.schemas.common import S3Key
from src.types.blur_types import BlurMethod, TimestampRanges


class BlurEveryoneRequest(BaseRequest):
    video_key: S3Key
    blur_method: BlurMethod
    output_key: S3Key
    timestamp_ranges: TimestampRanges

    @field_validator("timestamp_ranges")
    @classmethod
    def _validate_ranges(cls, v: TimestampRanges) -> TimestampRanges:
        if len(v) > MAX_TIMESTAMP_RANGES:
            raise ValueError(f"Too many timestamp ranges (max {MAX_TIMESTAMP_RANGES})")
        for start, end in v:
            if float(start) > float(end):
                raise ValueError(f"invalid range: start {start} > end {end}")
            if float(end) > MAX_TIMESTAMP_SECONDS:
                raise ValueError(f"range end {end} exceeds cap {MAX_TIMESTAMP_SECONDS}s")
        return v


class BlurEveryoneFilteredRequest(BlurEveryoneRequest):
    face_key: S3Key

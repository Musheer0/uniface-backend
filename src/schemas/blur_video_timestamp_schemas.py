from pydantic import BaseModel

from src.lib.blur_video_with_timestamps import TimestampRanges
from src.schemas.base_schema import BaseRequest
from src.types.blur_types import BlurMethod

class BlurEveryoneRequest(BaseRequest):
    video_key:str
    blur_method:BlurMethod
    output_key:str
    timestamp_ranges:TimestampRanges
class BlurEveryoneFilteredRequest(BlurEveryoneRequest):
    face_key:str
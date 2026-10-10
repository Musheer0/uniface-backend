from src.schemas.base_schema import BaseRequest
from src.schemas.common import S3Key
from src.types.blur_types import BlurMethod


class BlurEveryoneRequest(BaseRequest):
    video_key: S3Key
    blur_method: BlurMethod
    output_key: S3Key


class BlurEveryoneFilteredRequest(BlurEveryoneRequest):
    face_key: S3Key

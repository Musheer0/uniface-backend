from pydantic import BaseModel

from src.schemas.base_schema import BaseRequest
from src.types.blur_types import BlurMethod

class BlurEveryoneRequest(BaseRequest):
    img_key:str
    blur_method:BlurMethod
    output_key:str
class BlurEveryoneFilteredRequest(BlurEveryoneRequest):
    face_key:str
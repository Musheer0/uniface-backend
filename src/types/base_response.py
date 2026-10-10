from typing import Optional

from pydantic import BaseModel


class BaseRequest(BaseModel):
    user_id: str
    generation_id: str


class BaseResponse(BaseModel):
    success: bool
    generation_id: Optional[str] = None
    user_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

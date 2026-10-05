from pydantic import BaseModel

class BaseRequest(BaseModel):
    user_id:str
    generation_id:str
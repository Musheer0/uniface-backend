from fastapi import HTTPException, Header
import os
from dotenv import load_dotenv

load_dotenv()

def InternalAuthorization(api_key:str = Header()):
    if os.getenv("API_KEY")!= api_key:
        raise HTTPException(status_code=401,detail="Invalid Api Key")
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class RegisterService(BaseModel):
    name : str
    description : str

class AddRedirectUris(BaseModel):
    redirect_uris : List[HttpUrl]

class GetSerivceInfo(BaseModel):
    client_id : str
    name : str
    description : Optional[str]
    client_secret : str
    created_at : datetime
    owner : str
    redirect_uris : List[HttpUrl]
    
    class Config:
        from_attributes : True
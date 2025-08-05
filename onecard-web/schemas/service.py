from pydantic import BaseModel, HttpUrl
from typing import List

class RegisterService(BaseModel):
    name : str
    description : str

class AddRedirectUris(BaseModel):
    redirect_uris : List[HttpUrl]
    
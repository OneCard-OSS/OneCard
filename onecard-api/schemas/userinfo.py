from pydantic import BaseModel

class UserInfoResponse(BaseModel):
    sub:str
    name:str
    email:str
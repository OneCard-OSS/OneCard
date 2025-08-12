from pydantic import BaseModel

class RequestToken(BaseModel):
    grant_type:str
    client_secret:str
    redirect_uri:str
    code:str
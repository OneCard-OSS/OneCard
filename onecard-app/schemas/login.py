from pydantic import BaseModel

class InitiateLoginRequest(BaseModel):
    emp_no:str

class NfcVerifyRequest(BaseModel):
    attempt_id:str
    encrypted_data:str
    
class RefreshTokenRequest(BaseModel):
    refresh_token:str
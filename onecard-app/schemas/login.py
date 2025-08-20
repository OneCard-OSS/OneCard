from pydantic import BaseModel

class InitiateLoginRequest(BaseModel):
    emp_no:str

class EncryptedPayload(BaseModel):
    ciphertext:str

class NfcVerifyRequest(BaseModel):
    attempt_id:str
    pubkey:str
    encrypted_data:EncryptedPayload
    
class RefreshTokenRequest(BaseModel):
    refresh_token:str
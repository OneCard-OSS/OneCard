from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from core.database import get_db
from crud.login import login, verify_nfc, refresh_tokens, logout
from schemas.login import InitiateLoginRequest, NfcVerifyRequest, RefreshTokenRequest

app_login_router = APIRouter(prefix="/app/api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/app/api/verify")

@app_login_router.post("/initiate")
def initiate_login(request:InitiateLoginRequest, db:Session=Depends(get_db)):
    return login(emp_no=request.emp_no, db=db)

@app_login_router.post("/verify")
def verify_login(request:NfcVerifyRequest):
    return verify_nfc(
        attempt_id=request.attempt_id,
        pubkey_hex=request.pubkey,
        signature_hex=request.encrypted_data.model_dump()
    )

@app_login_router.post("/token")
def token(request:RefreshTokenRequest):
    return refresh_tokens(refresh_token=request.refresh_token)

@app_login_router.post("/logout")
def signout(access_token:str=Depends(oauth2_scheme)):
    return logout(access_token=access_token)
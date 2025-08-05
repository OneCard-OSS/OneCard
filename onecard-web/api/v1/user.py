from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from schemas.user import JoinUser, UserOut, LoginRequest
from crud.user.register import register_user
from crud.user.login import login, logout, issuedRefreshToken
from core.database import get_db

user_router = APIRouter(prefix="/api", tags=["Related Admin Page"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

@user_router.post("/register", response_model=UserOut, status_code=201)
def signup(new_user:JoinUser, db:Session=Depends(get_db)):
    '''
    Create an account via this API
    '''
    try:
        user = register_user(new_user=new_user, db=db)
        return UserOut(
            user_id=user.user_id,
            user_name=user.user_name,
            message="Successfully Created Account"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise e

@user_router.post("/login", status_code=200)
def signin(request:LoginRequest,
           token:Optional[str]=Depends(oauth2_scheme),
           db:Session=Depends(get_db)):
    return login(request=request, token=token, db=db)

@user_router.post("/logout", status_code=200)
def signout(token:str=Depends(oauth2_scheme)):
    return logout(token=token)

@user_router.post("/token", status_code=200)
def refresh(token:str=Depends(oauth2_scheme)):
    return issuedRefreshToken(token=token)
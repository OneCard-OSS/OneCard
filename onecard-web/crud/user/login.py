from fastapi import status, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional
from jose import JWTError
import datetime
import logging
from models.user import Users
from schemas.user import LoginRequest
from crud.user.register import verify_password
from core.token_instance import token_handler
from core.redis import redis_config

rd = redis_config()

def getUserInfo(user_id:str, db:Session):
    """
    Retrieve User Information using user_id
    Args:
    - user_id : User's ID
    - db: ORM Session
    Returns:
    - Users | None
    """
    return db.query(Users).filter(Users.user_id==user_id).first()

def login(request: LoginRequest,
          token: Optional[str],
          db: Session):
    """
    Admin Web Login Function
    Args:
    - request: Login DTO
    - token: access token
    - db: ORM Session
    Returns:
    - dict: status, token, token type, message
    """
    if token:
        if rd.get(f"blacklist:{token}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is blacklist"
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Already Logged In")
    user = getUserInfo(user_id=request.user_id, db=db)

    if not user or not verify_password(request.user_password, user.user_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID or password"
        )
    
    access_token = token_handler.create_access_token(
        data={"sub": str(user.id)}
    )
    refresh_token = token_handler.create_refresh_token(
        data={"sub":str(user.id)}
    )
    payload = token_handler.verify_token(token=refresh_token, is_refresh=True)
    exp = payload.get("exp")
    ttl = exp - int(datetime.datetime.now().timestamp()) # ttl = expire time - now
    rd.set(f"refresh_token:{user.id}", refresh_token, ex=ttl)
    
    return {
        "status" : status.HTTP_200_OK,
        "access_token": access_token, 
        "token_type": "bearer",
        "message" : "Login Success"
        }
    
def logout(token:str):
    """
    Admin Web logout
    access token blacklist
    Args:
    - token: access token
    Returns:
    - None
    """
    try:
        payload = token_handler.verify_token(token=token, is_refresh=False)
        exp = payload.get("exp")
        id = payload.get("sub")
        now = int(datetime.datetime.now().timestamp())
        ttl = max(exp-now, 0)
        if ttl > 0:
            rd.setex(f"blacklist:{token}", ttl, "true") # true: Blacklisted
        rd.delete(f"refresh_token:{id}")
    except HTTPException as he:
        logging.error(f"Error Occured:{he}")
    except Exception as e:
        raise e
    
def issuedRefreshToken(token:str):
    """
    Admin Web Issued Refresh Token
    
    Args:
    - token: refresh token
    
    Returns:
    - dict: access token, token type, expire time, message
    """
    payload = token_handler.verify_token(token=token, is_refresh=True)
    id = payload.get("sub")
    print(f"User ID:{id}")
    
    stored_refresh_token = rd.get(f"refresh_token:{id}")
    print(f"Refresh Token:{stored_refresh_token}")
    
    try:
        if not stored_refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Refresh Token Expired")
        stored_refresh_token = stored_refresh_token.decode('utf-8')
        if stored_refresh_token != token:
            raise HTTPException(status_code=401,
                                detail="Token Mismatch")
        blacklist = rd.get(f"blacklist:{token}")
        if blacklist:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid Refresh Token",
                                headers={"WWW-Authenticate" : "Bearer"})
        
        new_access_token = token_handler.create_access_token(data={"sub" : str(id)})
        
        return {
            "access_token" : new_access_token,
            "token_type" : "bearer",
            "expires_in" : payload.get("exp"),
            "message" : "Token Refreshed Successfully"
        } 
    except JWTError as je:
        logging.error(f"JWT Error:{str(je)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid Refresh Token",
                            headers={"WWW-Authenticate" : "Bearer"})
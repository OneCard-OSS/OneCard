from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from core.redis import redis_config
from core.token_instance import token_handler
import logging

rd = redis_config()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def current_user_info(token:str=Depends(oauth2_scheme)):
    try:
        if rd.get(f"blacklist:{token}"):
            raise HTTPException(status_code=401,
                                detail="Token has been revoked")
        payload = token_handler.verify_token(token=token, is_refresh=False)
        id = payload.get("sub")
        logging.debug(f"User ID:{id}")
        
        return {"id" : id}
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500,
                            detail="Error Occured while getting user info")
from fastapi import HTTPException
from sqlalchemy.orm import Session
from jose import JWTError
from typing import Dict, Any, Optional
from core.redis import redis_config
from core.token import Token
from models.service import Services
from utils.redis_const import REDIS_AUTH_CODE_PREFIX, REDIS_REFRESH_TOKEN_PREFIX, REDIS_SESSION_PUB_MAP_PREFIX, REDIS_PUB_SESSION_MAP_PREFIX
import json
import logging

token = Token()
rd = redis_config()

def handle_token_request(grant_type:str,
                         client_id:Optional[str],
                         client_secret:Optional[str],
                         redirect_uri:Optional[str],
                         code:Optional[str],
                         refresh_token:Optional[str],
                         db:Session):
    """
    Provide Access Token for User using Service
    Args:
    - request: access token을 얻기 위한 요청 DTO
    - db: ORM Session
    Returns:
    - blahblah 
    """
    try:
        # Branching logic based on grant_type and validation : access token
        if grant_type == "authorization_code":
            # 1-1. -- Token issuance via authorization code --
            if not code or not client_id or not client_secret or not redirect_uri:
                logging.warning("[/token] faild: Missing parameters for authorization_code grant")
                raise HTTPException(status_code=400,
                                    detail="Missing required parameters")
                
            # 1-2. Retrieve authorization code information from Redis
            auth_code_key = f"{REDIS_AUTH_CODE_PREFIX}{code}"
            raw_auth_data = rd.get(auth_code_key)
            if not raw_auth_data:
                logging.warning("[/token] faild: Invalid or Expired authorization code")
                raise HTTPException(status_code=400,
                                    detail="Invalid or Expired authorizatio code")
            
            auth_info:Dict[str, Any] = json.loads(raw_auth_data.decode('utf-8'))
            
            # 1-3. Retrieve service information from DB and verify client_secret
            services = db.query(Services).filter(Services.client_id == client_id).first()
            if not services or services.client_secret != client_secret:
                logging.warning(f"[/token] faild: Invalid client_secret for {client_id}")
                raise HTTPException(status_code=401,
                                    detail="Invalid client_id or client_secret")
            # 1-4. redirect_uri validation
            if auth_info.get("redirect_uri") != redirect_uri:
                logging.warning("[/token] faild: Mismatch redirect_uri")
                raise HTTPException(status_code=400,
                                    detail="Invalid redirect_uri")
            # 1-5. Authorization code has been used. Delete
            rd.delete(auth_code_key)
            
            # 1-6. Use s_id(Sessio ID) stored in authoriation code in accesstoken/refreshtoken claim
            s_id_for_token = auth_info.get("session")
            if not s_id_for_token:
                logging.error(f"[/token] faild: Session ID not include authorization code")
                raise HTTPException(status_code=404,
                                    detail="Session ID not include authorization cde")
            
            # 1-7. Issue Token
            access_token = token.create_access_token(data={"s_id":s_id_for_token})
            refresh_token = token.create_refresh_token(data={"s_id":s_id_for_token})
            
            # 1-8. Store refresh token in Redis
            # -- mapping: key(s_id):value(refresh_token)
            refresh_token_redis_key = f"{REDIS_REFRESH_TOKEN_PREFIX}{s_id_for_token}"
            refresh_token_ttl = token.RT_EXPIRE_MINUTES * 60
            rd.setex(refresh_token_redis_key, refresh_token_ttl, refresh_token)
            
            # 1-9. Session TTL updated
            session_key = f"{REDIS_SESSION_PUB_MAP_PREFIX}{s_id_for_token}"
            if rd.exists(session_key):
                rd.expire(session_key, refresh_token_ttl)
                raw_pubkey = rd.get(session_key)
                if raw_pubkey:
                    pubkey_s_id_key = f"{REDIS_PUB_SESSION_MAP_PREFIX}{raw_pubkey.decode('utf-8')}"
                    if rd.exists(pubkey_s_id_key):
                        rd.expire(pubkey_s_id_key, refresh_token_ttl)
            return {
                "token_type" : "bearer",
                "access_token" : access_token,
                "expires_in" : token.AT_EXPIRE_MINUTES * 60,
                "refresh_token" : refresh_token,
                "refresh_token_expires_in" : refresh_token_ttl
            }
        # Branching logic based on grant_type and validation : refresh token
        elif grant_type == "refresh_token":
            
            # -- Token renewal via refresh token --
            if not refresh_token or not client_id or not client_secret:
                logging.warning("[/token] failed: Missing parameters for refresh_token grant")
                raise HTTPException(status_code=400,
                                    detail="Missing required parameters")
            
            # Verify client_id and client_secret in DB
            services = db.query(Services).filter(
                Services.client_id == client_id,
                Services.client_secret == client_secret
            ).first()
            if not services:
                logging.warning("[/token] faild: Invalid client_id or client_secret")
                raise HTTPException(status_code=401, detail="Invalid client_id or client_secret")

            # Refresh Token validation and extract s_id
            try:
                payload = token.verify_token(token=refresh_token, is_refresh=True)
                s_id_for_token = payload.get("sub")
                if not s_id_for_token:
                    logging.warning("[/token] failed: RefreshToken payload missing sub")
                    raise HTTPException(status_code=401,
                                        detail="Invalid refresh token payload")
                # Verify that it matches token stored in Redis
                stored_refresh_token_key = f"{REDIS_REFRESH_TOKEN_PREFIX}{s_id_for_token}"
                stored_refresh_token = rd.get(stored_refresh_token_key)
                if not stored_refresh_token or stored_refresh_token.decode('utf-8') != refresh_token:
                    logging.warning(f"[/token] failed: Mismatch or expired refresh token for s_id: {s_id_for_token}")
                    rd.delete(stored_refresh_token_key) # Delete if token is invalid
                    raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
            except JWTError:
                logging.warning("[/token] failed: RefreshToken payload missing sub")
                raise HTTPException(status_code=401,
                                    detail="Invalid refresh token format")
            
            # Issue new access token
            new_access_token = token.create_access_token(data={"sub":s_id_for_token})
            refresh_token_ttl = rd.ttl(stored_refresh_token_key)
            
            # Update Token TTL
            if refresh_token_ttl > 0:
                rd.expire(stored_refresh_token_key, refresh_token_ttl)
            # Update Session TTL
            session_key = f"{REDIS_SESSION_PUB_MAP_PREFIX}{s_id_for_token}"
            if rd.exists(session_key):
                rd.expire(session_key, refresh_token_ttl)
                raw_pubkey = rd.get(session_key)
                if raw_pubkey:
                    pubkey_s_id_key = f"{REDIS_PUB_SESSION_MAP_PREFIX}{raw_pubkey.decode('utf-8')}"
                    if rd.exists(pubkey_s_id_key):
                        rd.expire(pubkey_s_id_key, refresh_token_ttl)
            return {
                "token_type" : "bearer",
                "access_token" : new_access_token,
                "expires_in" : token.AT_EXPIRE_MINUTES * 60,
                "refresh_token" : refresh_token,
                "refresh_token_expires_in" : refresh_token_ttl
            }
        else:
            logging.warning(f"[/token] failed: Unsupported grant type:{grant_type}")
            raise HTTPException(status_code=400,
                                detail="Unsupported grant type")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"[/token] Unexpected Error for code: {code}:{str(e)}")
        raise HTTPException(status_code=500,
                            detail="Error during token request")
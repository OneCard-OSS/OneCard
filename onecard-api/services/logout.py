from logging import LoggerAdapter
from core.redis import redis_config
from utils.redis_const import REDIS_REFRESH_TOKEN_PREFIX, REDIS_SESSION_PUB_MAP_PREFIX, REDIS_PUB_SESSION_MAP_PREFIX

rd = redis_config()

def logout_user(s_id:str,
                access_token:str,
                logger:LoggerAdapter):
    """
    Blacklist style logout
    Args:
    - s_id: User's session ID
    - access_token: Access token issued to the user
    Returns:
    - dict: message of success
    """
    logger.debug(f"Received token:{access_token}")
    # STEP 1. Verifying Token and Get session id
        
    # STEP 2. Delete refresh token and session in Redis
    refresh_token_key =  f"{REDIS_REFRESH_TOKEN_PREFIX}{s_id}"
    session_pub_key = f"{REDIS_SESSION_PUB_MAP_PREFIX}{s_id}"

    rd.delete(refresh_token_key)
    
    user_pubkey = rd.get(session_pub_key)
    if user_pubkey:
        pubkey_session_key = f"{REDIS_PUB_SESSION_MAP_PREFIX}{user_pubkey.decode('utf-8')}"
        rd.delete(pubkey_session_key)
        rd.delete(session_pub_key)
        logger.info("Session and RefreshToken successfully invalidated", extra={"s_id":s_id})
    else:
        logger.warning("Session key not found for s_id. Already logged out?", extra={"s_id":s_id})
    
    log_extra = {
        "s_id" : s_id,
        "action" : "logout",
        "status" : "success",
        "message" : "User logged out successfully"
    }
    logger.info("Logout process complete", extra=log_extra)

    return {"message" : "Logout Successful"}
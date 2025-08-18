from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from urllib.parse import urlencode
from models.service import Services, RedirectUris
from core.redis import redis_config
from utils.redirect_error import redirect_with_oauth2_error
from utils.redis_const import REDIS_AUTH_ATTEMPT_PREFIX, REDIS_AUTH_CODE_PREFIX
from logging import LoggerAdapter
import uuid
import json

rd = redis_config()

def get_authorization(response_type:str,
                      client_id:str,
                      redirect_uri:str,
                      state:Optional[str],
                      attempt_id:Optional[str],
                      db:Session,
                      logger:LoggerAdapter):
    """
    
    Args:
    - response_type: default "code"
    - client_id
    - redirect_uri
    - state: CSRF
    - attempt_id
    - db
    Returns:
    - RedirectResponse: Redirect to the redirect uri with authorization code passed as a parameter
    """
    s_id = None # User's OAuth Session ID
    attempt_state = None # Attempt State Information Save when using 
    redis_attempt_key = None
    
    # STEP 1. client_id and redirect_uri checking validation
    service = db.query(Services).join(
        RedirectUris, Services.client_id==RedirectUris.client_id
        ).filter(
            Services.client_id==client_id,
            RedirectUris.uris == redirect_uri
        ).first()
    if not service:
        logger.warning(f"Authorization failed: Invalid client_id or redirect_uri")
        raise HTTPException(status_code=401,
                            detail="Invalid client_id or redirect_uri")
    
    # STEP 2. response_type Checking
    if response_type != "code":
        logger.warning(f"Invalid response_type:{response_type}")
        return redirect_with_oauth2_error(redirect_uri=redirect_uri,
                                          status_code=400,
                                          detail="Invalid response type",
                                          state=state)
    # STEP 3. User Identification - attempt_id priority processing
    if attempt_id:
        redis_attempt_key = f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}"
        attempt_state = rd.get(redis_attempt_key)
        
        if not attempt_state:
            logger.warning(f"Invalid or Expire attempt_id")
            return redirect_with_oauth2_error(redirect_uri=redirect_uri,
                                              status_code=401,
                                              detail="Authentication attempt expired or invalid",
                                              state=state)
        try:
            attempt_state = json.loads(attempt_state.decode('utf-8'))
            logger.debug(f"Retrived attempt_state:{attempt_state}")
        except json.JSONDecodeError:
            logger.warning(f"JSON decode error for {attempt_id}")
            return redirect_with_oauth2_error(redirect_uri=redirect_uri,
                                              status_code=500,
                                              detail="Internal auth state error",
                                              state=state)
            
        if attempt_state.get("status") != "success":
            logger.warning(f"Attempt ID{attempt_id} is not success({attempt_state.get("status")})")
            return redirect_with_oauth2_error(redirect_uri=redirect_uri,
                                              status_code=403,
                                              detail="Authentication attempt not successful",
                                              state=state)
        matching_client_id = attempt_state.get("client_id")
        matching_redirect_uri = attempt_state.get("redirect_uri")
        matching_state = attempt_state.get("state")
        
        if matching_client_id != client_id or matching_redirect_uri != redirect_uri or (state is not None and matching_state != state):
            logger.warning(f"Mismatch request attempt_id")
            return redirect_with_oauth2_error(redirect_uri=redirect_uri,
                                              status_code=400,
                                              detail="Authorization request parameters mismatch the initial attempt",
                                              state=state)
            
        s_id = attempt_state.get("s_id")
        if not s_id:
            logger.warning(f"Session missing in successful attempt_state: {attempt_state}")
            return redirect_with_oauth2_error(redirect_uri=redirect_uri,
                                              status_code=500,
                                              detail="Internal auth state error: session missing",
                                              state=state)
        logger.debug(f"attempt_id authentication successful:{attempt_id} and s_id:{s_id}")
        
        rd.delete(redis_attempt_key)
        logger.debug(f"Deleted used attempt from Redis:{redis_attempt_key}")
    
    # STEP 4. Generating Authorization Code
    authorization_code = str(uuid.uuid4())
    
    # STEP 5. Save Authorization Code in Redis
    auth_data = {
        "code" : authorization_code,
        "client_id" : client_id,
        "redirect_uri" : redirect_uri,
        "state" : state,
        "session" : s_id
    }
    auth_code_ttl = 600 # Seconds
    redis_auth_code_key = f"{REDIS_AUTH_CODE_PREFIX}{authorization_code}"
    rd.setex(redis_auth_code_key, auth_code_ttl, json.dumps(auth_data))
    
    # STEP 6. Redirect the user's browser to the redirect_uri of the service server
    # Includ the issued Authorization Code in the query parameter
    redirect_query_params = {
        "code" : authorization_code,
        "state" : state
    }
    encoded_redirect_params = urlencode({k: v for k, v in redirect_query_params.items() if v is not None})
    redirect_url_with_code = f"{redirect_uri}?{encoded_redirect_params}"
    logger.info(f"Redirecting Browser to redirect_uri:{redirect_url_with_code}")
    
    return RedirectResponse(
        url=redirect_url_with_code,
        status_code=302
    )
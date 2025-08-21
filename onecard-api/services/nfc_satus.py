from fastapi import HTTPException
import json
import logging
from core.redis import redis_config
from utils.redis_const import REDIS_AUTH_ATTEMPT_PREFIX
from schemas.nfc import NfcStatusResponse

rd = redis_config()

def get_nfc_authentication_status(attempt_id:str,
                                  client_id:str):
    """
    Polls and retireve the current status of NFC authentication attempt
    Check Redis for a given attempt_id to determine 
    if NFC authentication is pending, successful, failed, or expired.
    Args:
    - attempt_id: unique identifier for login attempt
    - client_id: client_id of registered service
    Returns:
    - NfcStatusResponse: pydantic model containig status, error, error_description
    """
    try:
        redis_attempt_key = f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}"
        attempt_state = rd.get(redis_attempt_key)
        
        # STEP 1. attempt_id validation
        if not attempt_state:
            logging.warning("[/nfc-status] faild: Invalid or Expired attempt_id")
            return NfcStatusResponse(
                status="expired",
                error="attempt_expired",
                error_description="Authentication attempt expired or not exist"
            )
        attempt_state = json.loads(attempt_state.decode('utf-8'))
        
        # STEP 2. Check if client_id matches
        stored_cliet_id = attempt_state.get("client_id")
        if stored_cliet_id != client_id:
            logging.warning(f"[/nfc-status] faild: client_id mismatch for attempt:{attempt_id}")
            raise HTTPException(status_code=401,
                                detail="client_id mismatch")
        
        # STEP 3. Return a response including current status information
        status_response = NfcStatusResponse(
            status=attempt_state.get("status", "unknown status"),
            s_id=attempt_state.get("s_id"),
            error=attempt_state.get("error")
        )
        logging.debug(f"[/nfc-status] queried for attempt_id{attempt_id}: Status:{status_response.status}")
        
        return status_response
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"[/nfc-status] Unexpected Error for attempt:{str(e)}")
        raise HTTPException(status_code=500,
                            detail="Error Occured while retrieved NFC authentication status")
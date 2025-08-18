from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
import uuid
import time
from logging import LoggerAdapter
from models.pubkey import Pubkey
from schemas.card import CardDataRequest
from core.redis import redis_config
from core.token import Token 
from utils.redis_const import (
    REDIS_AUTH_ATTEMPT_PREFIX,
    REDIS_PUB_SESSION_MAP_PREFIX,
    REDIS_SESSION_PUB_MAP_PREFIX
)
from utils.decrypt import decrypted

rd = redis_config()
token = Token()

def verify_card_response(data:CardDataRequest, 
                         challenge:str, 
                         db:Session,
                         logger:LoggerAdapter):
    """
    Args:
    - data: CardData
    - challenge
    - db: ORM Session
    Returns:
    - public_key
    """
    try:
        decrypted = decrypted(data.card_data)
        public_key = decrypted.get("public key")
        response = decrypted.get("response")
        
        stored_challenge = challenge.upper()
        
        # STEP 1. Challenge Validation Check
        if stored_challenge != response:
            raise HTTPException(status_code=401,
                                detail="Invalid Response")
        logger.debug("Challenge correct match") 
        
        # STEP 2. Public key validation
        attempt_id = data.attempt_id
        private_key = rd.get(f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}")
        if public_key != private_key:
            pass
        
        # STEP 2. Verification of comparison between decrypted public key and public key stored in DB
        공개키담고있을테이블 = db.query(Pubkey).filter(Pubkey.pubkey == public_key).first()
        if not 공개키담고있을테이블:
            logger.warning(f"Pub key not found")
            raise HTTPException(status_code=404,
                                detail="Pub key not found")
        
        return public_key
    except Exception as e:
        logger.error(f"Unexpected Error while Verifying Card Data: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=str(e))
        
def get_card_response(data:CardDataRequest,
                      db:Session,
                      logger:LoggerAdapter):
    """
    Args:
    - data: DTO (card_data:str, attempt_id:str)
    - client_id
    - db
    """
    start_time = time.perf_counter()
    attempt_id = data.attempt_id
    logger.debug(f"Received raw data: {data.model_dump_json()}")
    
    redis_attempt_key = f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}"
    raw_attempt_state = rd.get(redis_attempt_key)
    attempt_state = None
    current_ttl = -3
    
    try:
        # STEP 1. Check attempt_id validity and status(pending)
        if not raw_attempt_state:
            logger.warning("Invalid or Expired attempt_id", extra={"attempt_id": attempt_id})
            raise HTTPException(status_code=401,
                                detail="Invalid or Expired authentication attempt")
        
        attempt_state = json.loads(raw_attempt_state.decode('utf-8'))
        current_ttl = rd.ttl(redis_attempt_key) 
        
        if attempt_state.get("status") != "pending":
            logger.warning(f"Attempt ID not pending, current_status:{attempt_state.get('status')}", extra={"attempt_id": attempt_id})
            raise HTTPException(status_code=400,
                                detail="Authentication attempt is not pending")
        
        # STEP 2. check client_id validity
        stored_client_id = attempt_state.get("client_id") 
        if stored_client_id != data.client_id:
            logger.warning(f"Client_id mismatch", extra={"attempt_id": attempt_id, "expected": stored_client_id, "received": data.client_id})
            raise HTTPException(status_code=401,
                                detail="client_id mismatch for this attempt")
        
        stored_attempt_challenge = attempt_state.get("challenge")
        if not stored_attempt_challenge:
            logger.error(f"Challenge missing in Redis State", extra={"attempt_id": attempt_id})
            raise HTTPException(status_code=500,
                                detail="Internal state error during verification")
            
        # STEP 3. NFC data verification and public key decryption
        decrypted_pub_key = verify_card_response(data=data.card_data, challenge=stored_attempt_challenge, db=db, logger=logger)
        
        # STEP 4. Look up a emp_no in Employee? Pubkey? DB using the decrypted public key
        pubkey_row = db.query(Pubkey).filter(Pubkey.pubkey == decrypted_pub_key).first()
        if not pubkey_row:
            logger.warning("NFC auth failed: User not found", extra={"attempt_id": attempt_id, "pub_key": decrypted_pub_key})
            raise HTTPException(status_code=404,
                                detail="User Not Found")
        
        logger.info(f"NFC authentication successful for pub_key {decrypted_pub_key}", extra={"attempt_id": attempt_id})
            
        # STEP 5. Generate internal Session ID in Authentication Server and Save in redis through mapping
        s_id = str(uuid.uuid4())
        session_ttl = token.RT_EXPIRE_MINUTES * 60
        
        rd.setex(f"{REDIS_SESSION_PUB_MAP_PREFIX}{s_id}",
                 session_ttl,
                 decrypted_pub_key)
        
        rd.setex(f"{REDIS_PUB_SESSION_MAP_PREFIX}{decrypted_pub_key}",
                 session_ttl,
                 s_id)
        logger.debug(f"Generated Session ID {s_id}", extra={"attempt_id": attempt_id})
             
        attempt_state["status"] = "success"
        attempt_state["s_id"] = s_id
        
        if current_ttl > -2:
            rd.setex(redis_attempt_key, max(current_ttl, 60) if current_ttl > 0 else 60,
                     json.dumps(attempt_state))
        else:
            logger.error(f"Attempt Key unexpectedly expired", extra={"attempt_id": attempt_id})
            raise HTTPException(status_code=500,
                                detail="Internal state error during verification")
        
        # STEP 7. OSTOOLS에게 성공 응답 반환
        response_time_ms = (time.perf_counter() - start_time) * 1000
        logger.info("Card response processed successfully", extra={"attempt_id": attempt_id, "response_time_ms": response_time_ms})
        
        return {"message" : "NFC Authentication Successful. Status updated"}
    except HTTPException as he: 
        logger.error(f"HTTPException raised: {he.detail}", extra={"attempt_id": attempt_id})
        raise he
    except Exception as e:
        logger.error(f"Unexpected error for attempt {attempt_id}, client_id {data.client_id}: {str(e)}", exc_info=True)
        if attempt_state is not None and current_ttl > -2:
            attempt_state["status"] = "failed"
            attempt_state["error"] = "Internal Error"
            attempt_state["error_description"] = "Unexpecteed server error occured during verification"
            rd.setex(redis_attempt_key, max(current_ttl, 60) if current_ttl > 0 else 60, json.dumps(attempt_state))
        
        raise HTTPException(status_code=500, detail="Internal Server Error")
from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
import uuid
import logging
from models.pubkey import Pubkey
from schemas.card import CardData, Card_data_with_attempt
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

def verify_card_response(data:CardData, 
                         challenge:str, 
                         db:Session):
    """
    Args:
    - data: CardData
    - challenge
    - db: ORM Session
    Returns:
    
    """
    try:
        decrypted = decrypted(data.card_data)
        pub_key = decrypted.get("public key")
        response = decrypted.get("response")
        
        stored_challenge = challenge.upper()
        
        # STEP 1. Challenge Validation Check
        if stored_challenge != response:
            raise HTTPException(status_code=401,
                                detail="Invalid Response")
        logging.debug("Challenge correct match") 
        
        # STEP 2. Verification of comparison between decrypted public key and public key stored in DB
        공개키담고있을테이블 = db.query(Pubkey).filter(Pubkey.pubkey == pub_key).first()
        if not 공개키담고있을테이블:
            logging.warning(f"Pub key not found")
            raise HTTPException(status_code=404,
                                detail="Pub key not found")
        
        return pub_key
    except Exception as e:
        logging.error(f"Unexpected Error while Verifying Card Data: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=str(e))
        
def get_card_response(data:Card_data_with_attempt, client_id, db:Session):
    """
    Args:
    - data
    - client_id
    - db
    """
    attempt_id = data.attempt_id
    logging.debug(f"[/card-response] received raw data: {data.model_dump_json()}")
    
    redis_attempt_key = f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}"
    raw_attempt_state = rd.get(redis_attempt_key)
    attempt_state = None
    current_ttl = -3
    
    try:
        # STEP 1. Check attempt_id validity and status(pending)
        if not raw_attempt_state:
            logging.warning("[/card-response] faild: Invalid or Expired attempt_id")
            raise HTTPException(status_code=401,
                                detail="Invalid or Expired authenticatio attempt")
        attempt_state = json.loads(raw_attempt_state.decode('utf-8'))
        current_ttl = rd.ttl(redis_attempt_key) # Get TTL for future update
        
        if attempt_state.get("status") != "pending":
            logging.warning(f"[/card-response] failed: attempt_id{attempt_id} not pending, current_status:{attempt_state.get('status')}")
            raise HTTPException(status_code=400,
                                detail="Authentication attempt is not pending")
        # STEP 2. check client_id validity
        stored_client_id = attempt_state.get("client_id") 
        if stored_client_id != client_id:
            logging.warning(f"[/card-response] failed: client_id mismatch for {attempt_id}")
            raise HTTPException(status_code=401,
                                detail="client_id mismatch for this attempt")
        stored_attempt_challenge = attempt_state.get("challenge")
        if not stored_attempt_challenge:
            logging.warning(f"[/card-response] failed: Chllenge for attempt missing in redis state:{attempt_id}")
            attempt_state["status"] = "failed"
            attempt_state["error"] = "Internal State Error"
            attempt_state["error_description"] = "Challenge Missing"
            if current_ttl > -2:
                rd.setex(redis_attempt_key, ...)
                raise HTTPException(status_code=500,
                                    detail="Internal state error during verification")
            
            # STEP 3. NFC data verification and public key decryption
            decrypted_pub_key = verify_card_response(data=data, challenge=stored_attempt_challenge, db=db)
            
            # STEP 4. Look up a emp_no in Employee? Pubkey? DB using the decrypted public key
            pubkey = db.query(Pubkey).filter(Pubkey.pubkey == decrypted_pub_key).first()
            if not pubkey:
                attempt_state["status"] = "failed"
                attempt_state["error"] = "User Not Found"
                attempt_state["error_description"] = "User associated with NFC card not found"
                
                # Reids State Update
                if current_ttl > -2:
                    rd.setex(redis_attempt_key, max(current_ttl, 60) if current_ttl > 0 else 60, json.dumps(attempt_state))
                
                logging.warning("[/card-response] NFC authentication failed for attempt")
                raise HTTPException(status_code=404,
                                    detail="User Not Found")
            logging.info(f"[/card-response] NFC authentication successful for {decrypted_pub_key}")
            
            # STEP 5. Generate internal Session ID in Authentication Server and Save in redis through mapping
            # s_id -> pubkey & pubkey -> s_id
            # Session lifetime matches the refresh token lifetime
            s_id = str(uuid.uuid4())
            session_ttl = token.RT_EXPIRE_MINUTES * 60
            
            rd.setex(f"{REDIS_SESSION_PUB_MAP_PREFIX}{s_id}",
                     session_ttl,
                     decrypted_pub_key)
            
            rd.setex(f"{REDIS_PUB_SESSION_MAP_PREFIX}{decrypted_pub_key}",
                     session_ttl,
                     s_id)
            logging.debug(f"[/card-response] Generated Session ID {s_id}, linked to pubkey:{decrypted_pub_key}")
             
            attempt_state["status"] = "success"
            attempt_state["s_id"] = s_id
            
            if current_ttl > -2:
                rd.setex(redis_attempt_key, max(current_ttl, 60) if current_ttl > 0 else 60,
                         json.dumps(attempt_state))
            else:
                logging.warning(f"[/card-response] Attempt Key unexpectly expired")
                raise HTTPException(status_code=500,
                                    detail="Internal state error during verification")
            
            return {"message" : "NFC Authentication Successful. Staus updated"}
    except HTTPException as he: 
        raise he
    except Exception as e:
        logging.error(f"[/card-response] Unexpected error for attempt {attempt_id}, client_id {client_id}:{str(e)}",
                      exc_info=True)
        if attempt_state is not None and current_ttl > -2:
            attempt_state["status"] = "failed"
            attempt_state["error"] = "Internal Error"
            attempt_state["error_description"] = "Unexpecteed server error occured during verification"
            rd.setex(redis_attempt_key, max(current_ttl, 60) if current_ttl > 0 else 60, json.dumps(attempt_state))
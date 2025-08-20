from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
import uuid
import time
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
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

rd = redis_config()
token = Token()
        
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
    log_extra = {"attempt_id": attempt_id, "client_id": data.client_id}
    logger.debug(f"Processing card response for attempt_id: {attempt_id}")

    # STEP 1: Check login attempt information in Redis
    redis_attempt_key = f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}"
    raw_attempt_state = rd.get(redis_attempt_key)
    
    if not raw_attempt_state:
        logger.warning("Invalid or Expired attempt_id", extra=log_extra)
        raise HTTPException(status_code=401,
                            detail="Invalid or Expired authentication attempt")
    
    attempt_state = json.loads(raw_attempt_state.decode('utf-8'))
    current_ttl = rd.ttl(redis_attempt_key)

    # STEP 2: Check request validation 
    if attempt_state.get("status") != "pending":
        log_extra["current_status"] = attempt_state.get('status')
        logger.warning("Attempt ID not pending", extra=log_extra)
        raise HTTPException(status_code=400,
                            detail="Authentication attempt is not pending")
    
    if attempt_state.get("client_id") != data.client_id:
        log_extra.update({"expected": attempt_state.get("client_id"), "received": data.client_id})
        logger.warning("Client_id mismatch", extra=log_extra)
        raise HTTPException(status_code=401,
                            detail="client_id mismatch for this attempt")

    # STEP 3: Lookup employee's public key in DB
    emp_no = attempt_state.get("emp_no")
    pubkey_record = db.query(Pubkey).filter(Pubkey.emp_no == emp_no).first()
    if not pubkey_record:
        logger.warning(f"Public key not found for emp_no: {emp_no}", extra=log_extra)
        raise HTTPException(status_code=404,
                            detail="Public key for this employee not found in DB.")
    
    card_pubkey_hex = pubkey_record.pubkey

    # STEP 4: Deriving a shared secret key and decrypting ciphertext
    try:
        server_private_key_value = int(attempt_state.get("server_private_key"), 16)
        original_challenge_bytes = bytes.fromhex(attempt_state.get("challenge"))
        
        server_private_key = ec.derive_private_key(server_private_key_value, ec.SECP256R1(), default_backend())
        card_public_key_bytes = bytes.fromhex(card_pubkey_hex)
        card_public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), card_public_key_bytes)
        
        shared_secret = server_private_key.exchange(ec.ECDH(), card_public_key)
        encryption_key = shared_secret[:16]

        # card_data is the challenge value encrypted and sent by the NFC card
        ciphertext = bytes.fromhex(data.card_data)
        
        cipher = Cipher(algorithms.AES(encryption_key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_challenge_bytes = unpadder.update(decrypted_padded_data) + unpadder.finalize()

    except Exception as e:
        logger.error(f"Decryption failed: {e}", extra=log_extra, exc_info=True)
        raise HTTPException(status_code=500,
                            detail="Decryption process failed.")

    # STEP 5: Challenge verification
    if decrypted_challenge_bytes[4:16] != original_challenge_bytes[4:16]:
        logger.warning("Challenge mismatch", extra=log_extra)
        raise HTTPException(status_code=401, 
                            detail="Challenge mismatch. Authentication failed.")
    
    logger.info(f"NFC authentication successful for emp_no {emp_no}", extra=log_extra)
            
    # STEP 6: Generate internal session ID and store mapping information in Redis
    s_id = str(uuid.uuid4())
    session_ttl = token.RT_EXPIRE_MINUTES * 60
    
    rd.setex(f"{REDIS_SESSION_PUB_MAP_PREFIX}{s_id}", session_ttl, card_pubkey_hex)
    rd.setex(f"{REDIS_PUB_SESSION_MAP_PREFIX}{card_pubkey_hex}", session_ttl, s_id)
    logger.debug(f"Generated Session ID {s_id}", extra=log_extra)
             
    # STEP 7: Update the attempt status stored in Redis to 'success'
    attempt_state["status"] = "success"
    attempt_state["s_id"] = s_id
    
    # Check if the Redis key has not expired and then update it.
    if current_ttl > -2:
        rd.setex(redis_attempt_key, max(current_ttl, 60) if current_ttl > 0 else 60,
                 json.dumps(attempt_state))
    else:
        logger.error("Attempt Key unexpectedly expired before status update", extra=log_extra)
        raise HTTPException(status_code=500,
                            detail="Internal state error: attempt expired prematurely.")
    
    response_time_ms = (time.perf_counter() - start_time) * 1000
    log_extra["response_time_ms"] = response_time_ms
    logger.info("Card response processed successfully", extra=log_extra)
    
    return {"message": "NFC Authentication Successful. Status updated"}
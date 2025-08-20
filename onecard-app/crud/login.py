from fastapi import HTTPException
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from jose import JWTError
from core.redis import redis_config
from core.token import Token
from models.employee import Employee
from models.pubkey import Pubkey
import datetime
import logging
import uuid
import os
import json

rd = redis_config()
token = Token()
APP_ATTEMPT_PREFIX="app_login_attempt:"
REFRESH_TOKEN_PREFIX = "app_refresh_token:"

def login(emp_no:str, db:Session):
    """
    Initiate Application Login
    request: LoginRequest(emp_no)
    """
    # STEP 1. Employee number validation
    employee = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    if not employee:
        raise HTTPException(status_code=400,
                            detail="Invalid Employee Number")
    
    # STEP 2. Generate a one-time ECC key pair on the server
    temporary_private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    temporary_public_key = temporary_private_key.public_key()
    
    server_public_key_bytes = temporary_public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # STEP 3. Generate 16 bytes challenge
    challenge = os.urandom(16)
    attempt_id = str(uuid.uuid4())
    
    # STEP 4. Store login request challenge in Redis(valid for 2 minutes)
    private_key_value = temporary_private_key.private_numbers().private_value()
    
    attepmt_state = {
        "emp_no" : emp_no,
        "server_private_key" : hex(private_key_value)[2:],
        "challenge" : challenge.hex()
    }
    rd.setex(f"{APP_ATTEMPT_PREFIX}", 120, json.dumps(attepmt_state))
    final_data = (server_public_key_bytes + challenge).hex()
    
    return {
        "attempt_id" : attempt_id,
        "response" : final_data
    }

def verify_nfc(attempt_id:str, 
               encrypted_challenge:str,
               db:Session):
    """
    After exchanging ECDH keys, the encrypted data is decrypted and verified 
    and if successful, a JWT token is issued
    Args:
    - attempt_id: Login attempt id
    - card_pubkey_hex: Employee's public key read from the card
    - encrypted_payload: containing ciphertext
    Returs:
    - dict: access token, refresh token, expire time, token type
    """
    
    # STEP 1. Check login attempt information in Redis
    attempt_key = f"{APP_ATTEMPT_PREFIX}{attempt_id}"
    attempt_data = rd.get(attempt_key)
    if not attempt_data:
        raise HTTPException(status_code=400,
                                detail="Login attempt expired or invalid")
    # The key is disposable. Delete it immediately
    rd.delete(attempt_key)
    
    attempt_data = json.loads(attempt_data)
    expected_emp_no = attempt_data.get("emp_no")
    server_private_key_value = int(attempt_data.get("server_private_key"), 16)
    original_challenge_bytes = bytes.fromhex(attempt_data.get("challenge"))
    
    # STEP 2. Lookup employee's public key in DB
    pubkey = db.query(Pubkey).filter(Pubkey.emp_no == expected_emp_no).first()
    if not pubkey:
        raise HTTPException(status_code=404,
                            detail="Public key for this employee not found")
    card_pubkey_hex = pubkey.pubkey
    
    # STEP 3. Deriving a shared secret key and decrypting ciphertext 
    try:
        server_private_key = ec.derive_private_key(server_private_key_value, ec.SECP256R1(), default_backend())
        card_public_key_bytes = bytes.fromhex(card_pubkey_hex)
        card_public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), card_public_key_bytes)
        
        # Generate shared secret 
        shared_secret = server_private_key.exchange(ec.ECDH(), card_public_key)
        
        # The first 128 bits (16 bytes) of the shared secret key are used directly as the encryption key
        encryption_key = shared_secret[:16]
        
        # Extract and decrypt the encrypted data sent by the client
        ciphertext = bytes.fromhex(encrypted_challenge)
        
        # Generate ciphter object and decryptor 
        cipher = Cipher(algorithms.AES(encryption_key), modes.ECB, backend=default_backend())
        decryptor = cipher.decryptor()
        
        # Run decryption
        decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove PKCS7 padding 
        # ECB mode is processes data in multiples of block size(128 bits) -> padding is required
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_challenge_bytes = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        
    except Exception as e:
        logging.warning(f"Decryption failed for attempt_id:{attempt_id}")
        raise HTTPException(status_code=500,
                            detail="Decryption failed")
    # STEP 4. Verification data: decrypted challenge matches original challenge
    if decrypted_challenge_bytes[4:16] != original_challenge_bytes[4:16]:
        raise HTTPException(status_code=401,
                            detail="Challenge mismatch. Authenticate failed")
    logging.info(f"NFC authentication successful for {expected_emp_no}")
    
    # STEP 5. Token issuance upon passing all verifications
    access_token = token.create_access_token({"sub":expected_emp_no})
    refresh_token = token.create_refresh_token({"sub":expected_emp_no})
    
    # STEP 6. Save refresh token in Redis
    refresh_token_key = f"{REFRESH_TOKEN_PREFIX}{expected_emp_no}"
    refresh_token_ttl = token.RT_EXPIRE_MINUTES * 60
    rd.setex(refresh_token_key, refresh_token_ttl, refresh_token)
    
    return {
        "access_token" : access_token,
        "refresh_token" : refresh_token,
        "token_type" : "bearer",
        "expires_in" : token.AT_EXPIRE_MINUTES * 60
    }

def refresh_tokens(refresh_token: str):
    """
    Verify the Refresh Token and issue a new Access Token and Refresh Token
    Args:
    - refresh_token: Received refresh token from client
    Returns:
    - dict: access token, refresh token, token type, expire time
    """
    try:
        payload = token.verify_token(token=refresh_token, is_refresh=True)
        emp_no = payload.get("sub")
        if not emp_no:
            raise HTTPException(status_code=401,
                                detail="Invalid refresh token payload")
             
        refresh_token_key = f"{REFRESH_TOKEN_PREFIX}{emp_no}"
        stored_token = rd.get(refresh_token_key)

        if not stored_token or stored_token.decode('utf-8') != refresh_token:
            # no token in redis or mismatch the received token -> immediately delete 
            if stored_token:
                rd.delete(refresh_token_key)
            raise HTTPException(status_code=401,
                                detail="Refresh token is invalid or has been revoked")

        # Rotation
        new_access_token = token.create_access_token(data={"sub": emp_no})
        new_refresh_token = token.create_refresh_token(data={"sub": emp_no})

        # Store a new refresh token in Redis (maintain the existing TTL)
        ttl = rd.ttl(refresh_token_key)
        if ttl > 0:
            rd.setex(refresh_token_key, ttl, new_refresh_token)
        else:
            default_ttl = token.RT_EXPIRE_MINUTES * 60
            rd.setex(refresh_token_key, default_ttl, new_refresh_token)

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": token.AT_EXPIRE_MINUTES * 60
        }

    except JWTError as je:
        logging.error(f"Invalid refresh token:{je}")
        raise HTTPException(status_code=401,
                            detail="Invalid refresh token.")

def logout(access_token:str):
    """
    Blakclist style logout
    Args:
    - access_token: access token sent when user logout
    Returns:
    - dict: successful message
    """
    try:
        payload = token.verify_token(token=token, is_refresh=False)
        emp_no = payload.get("sub")
        if not emp_no:
            raise HTTPException(status_code=401,
                                detail="Invalid access token payload")
        
        exp = payload.get("exp")
        now = int(datetime.datetime.now().timestamp())
        ttl = max(exp-now, 0)
        if ttl > 0:
            rd.setex(f"blacklist:{access_token}", ttl, "true")
        
        refresh_token_key = f"{REFRESH_TOKEN_PREFIX}{emp_no}"
        
        rd.delete(refresh_token_key)
        
        return {"message" : "Logout successful"}
    except JWTError as je:
        logging.error(f"Logout attempt with invalid token:{je}")
        return {"message" : "Token is already invalid. Logged out"}
        
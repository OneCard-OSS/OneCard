from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from core.redis import redis_config
from core.conn_noti_server import notification_server_communication
from models.service import Services, RedirectUris
from models.employee import Employee
from utils.redis_const import REDIS_AUTH_ATTEMPT_PREFIX
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from logging import LoggerAdapter
import time
import uuid
import json
import os
rd = redis_config()

async def init_login(emp_no:str,
                     client_id:str,
                     redirect_uri:str,
                     db:Session,
                     logger:LoggerAdapter,
                     state:Optional[str]=None,):
    """
    The first login function used by the authentication server.
    Login is performed via an HTML file that responds from the authentication server.
    Args:
    - client_id: client_id of registered service
    - emp_no: Personal employee number of user logging into service (used as an ID)
    - redirect_uri: redirect URI of service registered on authentication server
    - db: ORM Session
    - state: CSRF 
    - logger: LoggerAdapter-Perform logging with additional context information such as endpoints
    Returns:
    - dict: Result about message Push Notification Server 
    """
    start_time = time.perf_counter()
    
    emp = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    
    service = db.query(Services).join(RedirectUris).filter(
        Services.client_id == RedirectUris.client_id,
        RedirectUris.uris == redirect_uri
    ).first()
    
    if not service:
        log_extra = {"client_id": client_id, "emp_no": emp_no, "status": "failed", "error_message": "Not found client_id or redirect_uri"}
        logger.warning("Not found client_id or redirect_uri", extra=log_extra)
        raise HTTPException(status_code=404,
                            detail="Not found client_id or redirect_uri")
    log_extra = {
        "service_name" : service.name,
        "client_id" : client_id,
        "emp_no" : emp.emp_no,
        "status" : "success"
    } 
    if not emp:
        log_extra.update({"status" : "failed", "error_message" : "Invalid emp_no"})
        logger.warning("Invalid emp_no provided", extra=log_extra)
        raise HTTPException(status_code=400,
                            detail="Invalid emp_no")
    if emp in service.employees:
        log_extra.update({"status" : "failed", "error_message" : "Access denied for this service"})
        logger.warning("Attempted login by a blocked employee", extra=log_extra)
        raise HTTPException(status_code=403,
                            detail="You do not have permission to access this service")
    attempt_id = str(uuid.uuid4())
    logger.debug(f"Generated attemp_id:{attempt_id}")
    
    # --- ECC Challenge Generating ---
    # STEP 1. ECC key pair generate (SECP256R1)
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()
    
    # STEP 2. Format the public key as 65 bytes (0x04 + x + y)
    server_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    
    # STEP 3. Generate a 16 byte random challenge
    challenge = os.urandom(16)
    
    # STEP 4. Final data to be transmitted (65 bytes + 16 bytes = 81 bytes)
    final_data = (server_public_key + challenge).hex()
    
    # STEP 5. Store private key and challenge in Redis for later verification
    prviate_key_value = private_key.private_numbers().private_value
    attempt_state = {
        "status" : "pending",
        "emp_no" : emp_no,
        "client_id" : client_id,
        "redirect_uri" : redirect_uri,
        "state" : state,
        "s_id" : None,
        "server_private_key" : hex(prviate_key_value)[2:],
        "challenge" : challenge.hex()
    }
    logger.debug(f"Attempt State: {attempt_state}")
    attempt_ttl = 300 # Seconds
    attempt_redis_key = f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}"
    rd.setex(attempt_redis_key, attempt_ttl, json.dumps(attempt_state))
    try:
        await notification_server_communication(attempt_id=attempt_id,
                                                emp_no=emp_no, 
                                                client_id=client_id,
                                                service_name=service.name,
                                                data=final_data)
    except HTTPException as he:
        log_extra.update({"status": "failed", "error_message": he.detail})
        logger.error("Notification server communication failed", extra=log_extra)
        raise he
    except Exception as e:
        log_extra.update({"status": "failed", "error_message": str(e)})
        logger.error("Unexpected error occured", extra=log_extra)
        raise HTTPException(status_code=500, detail="Unexpected error occured")
    
    response_time_ms = (time.perf_counter() - start_time) * 1000
    log_extra["response_time_ms"] = response_time_ms
    logger.info("Login process completed successfully", extra=log_extra)
    
    return {
        "status" : 200,
        "message" : "Data delivered to push server successfully",
        "pub_data" : attempt_id
    }

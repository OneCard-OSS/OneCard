from fastapi import HTTPException
from sqlalchemy.orm import Session
from core.redis import redis_config
from core.conn_noti_server import notification_server_communication
from models.service import Services, RedirectUris
from models.employee import Employee
from utils.redis_const import REDIS_AUTH_ATTEMPT_PREFIX
import logging
import uuid
import random
import json

rd = redis_config()

async def init_login(emp_no:str,
               client_id:str,
               redirect_uri:str,
               db:Session):
    """
    OneCard API Init Login -> 사원번호 사용(더미데이터 만들기)
    Args:
    - client_id
    - emp_no
    - redirect_uri
    - db
    Returns:
    - dict: Result about message Push Notification Server 
    """
    logging.debug(f"Entering init login data:{emp_no}, client_id:{client_id}")
    emp = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    
    if not emp:
        raise HTTPException(status_code=400,
                            detail="Invalid emp_no")
    service = db.query(Services).join(RedirectUris).filter(
        Services.client_id == RedirectUris.client_id,
        RedirectUris.uris == redirect_uri
    ).first()
    if not service:
        raise HTTPException(status_code=404,
                            detail="Not found client_id or redirect_uri")
    attempt_id = str(uuid.uuid4())
    logging.debug(f"Generated attemp_id:{attempt_id}")
    
    new_attempt_challenge = hex(random.getrandbits(2048))[2:].zfill(512)
    logging.debug(f"[/v1/login] Generated Challenge:{new_attempt_challenge}")
    
    attempt_state = {
        "status" : "pending",
        "client_id" : client_id,
        "redirect_uri" : redirect_uri,
        "s_id" : None,
        "challenge" : new_attempt_challenge
    }
    attempt_ttl = 300 # Seconds
    attempt_redis_key = f"{REDIS_AUTH_ATTEMPT_PREFIX}{attempt_id}"
    rd.setex(attempt_redis_key, attempt_ttl, json.dumps(attempt_state))
    
    noti_data = await notification_server_communication(attempt_id=attempt_id,
                                                  emp_no=emp_no, 
                                                  client_id=client_id,
                                                  challenge=new_attempt_challenge)
    logging.debug(f"Notification Data:{noti_data}")
    
    return {
        "status" : 200,
        "message" : "Data delivered to push server successfully",
        "pub_data" : attempt_id
    }

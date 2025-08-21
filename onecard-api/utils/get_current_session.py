from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.employee import Employee
from models.pubkey import Pubkey
from core.token import Token
from core.redis import redis_config
from utils.redis_const import REDIS_SESSION_PUB_MAP_PREFIX

token_handler = Token()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
rd = redis_config()

def get_employee_from_session_id(s_id:str, db:Session)->Employee:
    """
    Query Redis and database using session id(s_id)
    Return the corresponding Employee ORM object
    """
    pubkey_hex = rd.get(f"{REDIS_SESSION_PUB_MAP_PREFIX}{s_id}")
    if not pubkey_hex:
        raise HTTPException(status_code=404, 
                            detail="User session not found in Redis")
    pubkey = db.query(Pubkey).filter(Pubkey.pubkey == pubkey_hex.decode('utf-8')).first()
    if not pubkey or not pubkey.employee:
        raise HTTPException(status_code=404, detail="User not found in DB for the given session")
    return pubkey.employee

async def get_current_session(token: str = Depends(oauth2_scheme)):
    """
    [수정됨] Authorization 헤더에서 Bearer 토큰을 추출하고 검증하여
    내부 세션 ID(s_id)를 반환합니다.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # verify_token 함수는 JWTError를 발생시킬 수 있습니다.
        payload = token_handler.verify_token(token=token, is_refresh=False)
        s_id = payload.get("sub")
        if s_id is None:
            raise credentials_exception
        return s_id
    except Exception: # JWTError 포함 모든 예외 처리
        raise credentials_exception
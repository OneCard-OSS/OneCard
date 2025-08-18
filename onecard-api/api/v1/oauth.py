from fastapi import APIRouter, Query, Depends, Form, HTTPException
from jose import JWTError
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from core.token import Token
from services.get_authorization import get_authorization
from services.token_service import handle_token_request
from services.logout import logout_user
from logging import getLogger
from logging_config import EndPointAdapter

token = Token()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")
oauth_router = APIRouter(prefix="/api/v1", tags=["OAuth API"])

@oauth_router.get("/authorize")
def authorize(response_type:str=Query(...),
              client_id:str=Query(...),
              redirect_uri:str=Query(...),
              state:Optional[str]=Query(None),
              attempt_id:Optional[str]=Query(None),
              db:Session=Depends(get_db)):
    
    logger = getLogger(__name__)
    adapter = EndPointAdapter(logger, {"endpoint":"GET /api/v1/authorize"})
    
    return get_authorization(response_type=response_type,
                             client_id=client_id,
                             redirect_uri=redirect_uri,
                             state=state,
                             attempt_id=attempt_id,
                             db=db,
                             logger=adapter)
    
@oauth_router.post("/token")
def token(
    grant_type: str = Form(..., description="The type of grant being requested. 'authorization_code' or 'refresh_token'."),
    client_id: str = Form(..., description="The service's unique identifier."),
    client_secret: str = Form(..., description="The service's secret key."),
    redirect_uri: Optional[str] = Form(None, description="The redirection URI used in the initial authorization request."),
    code: Optional[str] = Form(None, description="The authorization code received from the authorization endpoint."),
    refresh_token: Optional[str] = Form(None, description="The refresh token issued to the client."),
    db: Session = Depends(get_db)):
    """
    Handles token requests for both Authorization Code and Refresh Token grants.
    """
    logger = getLogger(__name__)
    adapter = EndPointAdapter(logger, {"endpoint":"POST /api/v1/token"})
    
    return handle_token_request(
        grant_type=grant_type,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        code=code,
        refresh_token=refresh_token,
        db=db,
        logger=adapter
    )

@oauth_router.post("/logout")
def logout(access_token:str=Depends(oauth2_scheme)):
    logger = getLogger(__name__)
    adapter = EndPointAdapter(logger, {"endpoint" : "POST /api/v1/logout"})
    try:
        payload = token.verify_token(access_token, is_refresh=False)
        s_id = payload.get("sub")
        if not s_id:
            adapter.warning(f"Invalid Session ID", extra={"payload":payload})
            raise HTTPException(status_code=401,
                                detail="Invalid Session ID")
        return logout_user(s_id=s_id, access_token=access_token, logger=adapter)
    except JWTError as je:
        logger.error(f"JWTError Occured: {str(je)}")
        raise HTTPException(status_code=401,
                            detail="Invalid Token")
    except Exception as e:
        adapter.error(f"Unexpected error during logout:{str(e)}", exc_info=True)
        raise HTTPException(status_code=500,
                            detail="Internal Server Error")
from fastapi import APIRouter, Query, Depends, Form
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from services.get_authorization import get_authorization
from services.token_service import handle_token_request

oauth_router = APIRouter(prefix="/api/v1", tags=["OAuth API"])

@oauth_router.get("/authorize")
def authorize(response_type:str=Query(...),
              client_id:str=Query(...),
              redirect_uri:str=Query(...),
              state:Optional[str]=Query(None),
              attempt_id:Optional[str]=Query(None),
              db:Session=Depends(get_db)):
    
    return get_authorization(response_type=response_type,
                             client_id=client_id,
                             redirect_uri=redirect_uri,
                             state=state,
                             attempt_id=attempt_id,
                             db=db)
    
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
    return handle_token_request(
        grant_type=grant_type,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        code=code,
        refresh_token=refresh_token,
        db=db
    )
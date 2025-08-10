from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional
from core.database import get_db
from services.get_authorization import get_authorization

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
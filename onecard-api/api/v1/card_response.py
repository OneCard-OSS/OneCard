from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.card_response import get_card_response
from schemas.card import CardDataRequest
from logging import getLogger
from logging_config import EndPointAdapter

card_response_router = APIRouter(prefix="/api/v1", tags=["NFC tagging response"])

@card_response_router.post("/card-response")
def card_response(data:CardDataRequest, 
                  db:Session=Depends(get_db)):
    
    logger = getLogger(__name__)
    adapter = EndPointAdapter(logger, {"endpoint":"POST /api/v1/card-response"})
    
    return get_card_response(data=data,  
                             db=db,
                             logger=adapter)
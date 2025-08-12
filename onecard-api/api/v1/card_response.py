from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.card_response import get_card_response

card_response_router = APIRouter(prefix="/api/v1", tags=["NFC tagging response"])

@card_response_router.post("/card-response")
def card_response(data, client_id, db:Session=Depends(get_db)):
    return get_card_response(data=data, client_id=client_id, db=db)
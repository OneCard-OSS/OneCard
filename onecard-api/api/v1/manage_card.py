from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.manage_card import manage_card
from schemas.card import ManageCard
card_router = APIRouter(prefix="/api/v1")

@card_router.post("/card")
def management_card(request:ManageCard,
                    db:Session=Depends(get_db)):
    
    return manage_card(request=request, db=db)
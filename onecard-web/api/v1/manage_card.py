from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from crud.register_card.manage_card import manage_card
from schemas.card import ManageCard
from utils.current_user import current_user_info

card_router = APIRouter(prefix="/api/v1", tags=["Manage Employee Card"])

@card_router.post("/card")
def management_card(request:ManageCard,
                    db:Session=Depends(get_db),
                    current_user=Depends(current_user_info)):
    
    return manage_card(request=request, db=db, current_user=current_user)
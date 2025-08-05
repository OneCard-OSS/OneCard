from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from crud.service.register import create_service, add_redirect_uris
from utils.current_user import current_user_info
from schemas.service import RegisterService, AddRedirectUris

service_router = APIRouter(prefix="/api", tags=["Related Register OneCard Service"])

@service_router.post("/services")
def register_service(service:RegisterService,
                     db:Session=Depends(get_db),
                     current_user=Depends(current_user_info)):
    
    return create_service(service=service, db=db, current_user=current_user)

@service_router.post("/services/{client_id}/redirect-uris")
def register_redirect_uris(client_id:str,
                           uris:AddRedirectUris,
                           db:Session=Depends(get_db),
                           current_user=Depends(current_user_info)):
    
    return add_redirect_uris(client_id=client_id,
                             uris=uris,
                             db=db,
                             current_user=current_user)
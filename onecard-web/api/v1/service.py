from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from core.database import get_db
from crud.service.register import create_service, add_or_update_redirect_uris
from crud.service.get_service import get_service
from crud.service.remove_service import remove_service
from utils.current_user import current_user_info
from schemas.service import RegisterService, AddRedirectUris, GetSerivceInfo

service_router = APIRouter(prefix="/api", tags=["Related Register OneCard Service"])

@service_router.get("/{service_name}", response_model=GetSerivceInfo)
def get_servicee_info(service_name:str,
                      db:Session=Depends(get_db),
                      current_user=Depends(current_user_info)):
    
    return get_service(service_name=service_name, db=db, current_user=current_user)

@service_router.post("/services")
def register_service(service:RegisterService,
                     db:Session=Depends(get_db),
                     current_user=Depends(current_user_info)):
    
    return create_service(service=service, db=db, current_user=current_user)

@service_router.post("/services/redirect-uris/{client_id}")
async def register_redirect_uris(client_id:str,
                           uris:AddRedirectUris,
                           request:Request,
                           db:Session=Depends(get_db),
                           current_user=Depends(current_user_info)):
    raw_body = await request.body()
    print(f"Raw body bytes: {raw_body}")  # 바이너리 출력
    print(f"Decoded raw body: {raw_body.decode('utf-8', errors='replace')}")  # 디코딩 시도
    print(f"Parsed uris: {uris}")
    return add_or_update_redirect_uris(client_id=client_id,
                                       uris=uris,
                                       db=db,
                                       current_user=current_user)

@service_router.delete("/services/{client_id}", status_code=200)
def delete_service(client_id:str,
                   db:Session=Depends(get_db),
                   current_user=Depends(current_user_info)):
    
    return remove_service(client_id=client_id, db=db, current_user=current_user)
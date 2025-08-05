from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from models.user import Users
from models.service import Services, RedirectUris
from schemas.service import RegisterService, AddRedirectUris
from utils.current_user import current_user_info
from utils.gen import gen_client_secret, gen_client_id

def create_service(service:RegisterService, 
                     db:Session,
                     current_user:dict):
    id = current_user["id"]
    print(f"User ID:{id}")
    if not id:
        raise HTTPException(status_code=400,
                            detail="Invalid User")
    client_id = gen_client_id()
    client_secret = gen_client_secret()
        
    new_service = Services(
        client_id = client_id,
        client_secret = client_secret,
        owner_id = id,
        name = service.name,
        description = service.description
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    
    return new_service 
        
def add_redirect_uris(client_id:str,
                      uris:AddRedirectUris, 
                      db:Session,
                      current_user:dict):
    id = current_user["id"]
    service = db.query(Services).filter(Services.client_id == client_id,
                                        Services.owner_id == id).first()
    if not service:
        raise HTTPException(status_code=404,
                            detail="Service not found or don't have permission to modify it")
    for uri in uris.redirect_uris:
        redirect_uri = RedirectUris(client_id=service.client_id,
                                    uris=str(uri)
        )
        db.add(redirect_uri)
    
    db.commit()
    return {"message" : "Redirect URIs registered successfully"}
        
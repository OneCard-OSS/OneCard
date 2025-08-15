from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from models.service import Services, RedirectUris
from schemas.service import RegisterService, AddRedirectUris
from utils.gen import gen_client_secret, gen_client_id

def create_service(service:RegisterService, 
                     db:Session,
                     current_user:dict):
    """
    If you are a logged in administrator, you can register.
    Create a new service.
    Args:
    - service: Register DTO containing service registration details(name, description)
    - db: ORM Session
    - current_user: JWT-based current user information
    Returns:
    - Services: The newly created service ORM object
    """
    
    client_id = gen_client_id()
    client_secret = gen_client_secret()
        
    new_service = Services(
        client_id = client_id,
        client_secret = client_secret,
        owner_id = current_user["id"],
        name = service.name,
        description = service.description
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    
    return new_service 
        
def add_or_update_redirect_uris(client_id:str,
                                uris:AddRedirectUris, 
                                db:Session,
                                current_user:dict):
    """
    Add or Update redirect URIs for a given service.
    This function allows only the administrator 
    who registered the service to manipulate the redirect URIs.
    
    Args:
    - client_id: The client ID of the service
    - uris: DTO containing the list of redirect URIs to register
    - db: ORM Session
    - current_user: JWT-based current user information
    Returns:
    - dict: Confirmation message indicating success
    """
    
    service = db.query(Services).filter(Services.client_id == client_id).first()
    if not service:
        raise HTTPException(status_code=404,
                            detail="Service not found")
    if  UUID(current_user["id"]) != service.owner_id:
        raise HTTPException(status_code=403,
                            detail="Permission denied")
    
    db.query(RedirectUris).filter(RedirectUris.client_id == client_id).delete()
    
    for uri in set(uris.redirect_uris):
        redirect_uri = RedirectUris(client_id=service.client_id,
                                    uris=str(uri))
        db.add(redirect_uri)
    db.commit()
    return {"message" : f"Successfully added Redirect URIs"}
    
    # exisiting_uris = {uri.uris for uri in service.redirect_uris}
    # new_uris_added = 0
    # for uri in uris.redirect_uris:
    #     uri_str = str(uri)
    #     if uri_str not in exisiting_uris:
    #         redirect_uri = RedirectUris(client_id=service.client_id,
    #                                     uris=str(uri))
    #         db.add(redirect_uri)
    #         new_uris_added += 1
    # if new_uris_added > 0:
    #     db.commit()
    #     return {"message" : f"Successfully added {new_uris_added} Redirect URIs"}
    # else:
    #     return {"message" : "No new URI to add or URI is already registered"}
    
    
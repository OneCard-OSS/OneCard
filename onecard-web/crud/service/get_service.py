from fastapi import HTTPException
from sqlalchemy.orm import Session
import math
from models.service import Services
from schemas.service import GetSerivceInfo

def get_service(service_name:str,
                 db:Session,
                 current_user:dict):
    service = db.query(Services).filter(Services.name == service_name).first()

    if not service:
        raise HTTPException(status_code=404,
                            detail="Service not found")
    
    return GetSerivceInfo(
        client_id=service.client_id,
        name=service.name,
        description=service.description,
        client_secret=service.client_secret,
        created_at=service.created_at,
        owner=service.owner.user_name,
        redirect_uris=[uri.uris for uri in service.redirect_uris]
    )

def get_paginated_services(db:Session, page:int=1, page_size:int=10):
    """
    View a list of services using pagination
    """
    if page < 1:
        page = 1
    skip = (page - 1) * page_size
    total_services = db.query(Services).count()
    services = db.query(Services).offset(skip).limit(page_size).all()
    total_pages = math.ceil(total_services / page_size)
    return {
        "services" : services,
        "total_pages" : total_pages,
        "current_page" : page
    }
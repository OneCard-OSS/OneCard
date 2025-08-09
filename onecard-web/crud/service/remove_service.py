from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from models.service import Services

def remove_service(client_id:str,
                   db:Session,
                   current_user:dict):
    service = db.query(Services).filter(Services.client_id==client_id).first()
        
    if not service:
        raise HTTPException(status_code=404,
                            detail="Registered Service is not found")
    if UUID(current_user["id"]) != service.owner_id:
        raise HTTPException(status_code=403,
                            detail="Only the owner can delete this service")
    db.delete(service)
    db.commit()
    
    return {"message" : "Serivce deleted successfully"}
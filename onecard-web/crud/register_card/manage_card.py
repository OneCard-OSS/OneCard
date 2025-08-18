from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.employee import Employee
from models.pubkey import Pubkey
from schemas.card import ManageCard
import logging

def manage_card(request:ManageCard, db:Session, current_user:dict):
    """
    Manage ID Card
    Register Card from Qt
    """
    emp = db.query(Employee).filter(Employee.emp_no == request.emp_no).first()
    if not emp:
        raise HTTPException(status_code=404,
                            detail="Employee number not found")
    if request.existing:
        # Update existing public key
        existing_pubkey = db.query(Pubkey).filter(Pubkey.emp_no == request.emp_no).first()
        if not existing_pubkey:
            raise HTTPException(status_code=404,
                                detail="No existing public key found for this employee to update")
        existing_pubkey.pubkey = request.pubkey
        db.commit()
        db.refresh(existing_pubkey)
        logging.info(f"Updated public key for emp_no:{request.emp_no}")
        return {"message" : f"Successfully updated public key {request.emp_no}"}
    else:
        pubkey_data = Pubkey(
            pubkey=request.pubkey,
            emp_no=request.emp_no
        )
        try:
            db.add(pubkey_data)
            db.commit()
            db.refresh(pubkey_data)
        except IntegrityError:
            db.rollback()
            logging.warning(f"Pubkey already exists for emp_no:{request.emp_no}")
            raise HTTPException(status_code=400,
                                detail="Public key already existed for this employee")
        logging.info(f"Registered Information to Pubkey Database Successfully")
        return {"message" : f"Registered Public key successfully by {request.emp_no}"}

from fastapi import HTTPException
from sqlalchemy.orm import Session
from utils.get_hashed import get_hashed_pub_key
from models.employee import Employee
from models.pubkey import Pubkey
from schemas.card import ManageCard
import logging

def manage_card(request:ManageCard, db:Session):
    """
    Manage ID Card
    Register Card from Qt
    """
    emp = db.query(Employee).filter(Employee.emp_no == request.emp_no).first()
    if not emp:
        raise HTTPException(status_code=404,
                            detail="Employee number not found")
    hashed_pub_key = get_hashed_pub_key(request.pubkey)
    pubkey_data = Pubkey(
        pubkey = hashed_pub_key,
        emp_no = request.emp_no
    )
    db.add(pubkey_data)
    db.commit()
    db.refresh(pubkey_data)
    logging.info(f"Registered Information to Pubkey Database Successfully")
    return pubkey_data

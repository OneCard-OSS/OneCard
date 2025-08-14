from sqlalchemy.orm import Session
from models.pubkey import Pubkey
import hashlib

def get_hashed_pub_key(plain_pub_key:str):
    hashed = hashlib.sha256(plain_pub_key.encode()).hexdigest()
    return hashed

def verify_pubkey(emp_no:str, plain_pub_key:str, db:Session):
    
    hashed_pub_key = get_hashed_pub_key(plain_pub_key=plain_pub_key)
    stored_pubey = db.query(Pubkey).filter(Pubkey.emp_no == emp_no).first()
    
    if stored_pubey.pubkey == hashed_pub_key:
        return True
    else:
        return False
    
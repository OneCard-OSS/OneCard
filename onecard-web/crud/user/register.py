from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from schemas.user import JoinUser
from models.user import Users

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register_user(new_user:JoinUser, db:Session) -> Users:
    try:
        # Check if User ID Exists
        if db.query(Users).filter(Users.user_id == new_user.user_id).first():
            raise HTTPException(status_code=409,
                                detail="User ID already exists")
            
        hashed_password = bcrypt_context.hash(new_user.user_password)
        import uuid
        user = Users(
            id = uuid.uuid4(), 
            user_id = new_user.user_id,
            user_password = hashed_password,
            user_name = new_user.user_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"{e}")

def verify_password(plain_password : str, hashed_password : str) -> bool:
    return bcrypt_context.verify(plain_password, hashed_password)
        


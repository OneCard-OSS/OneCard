from jose import jwt, JWTError
from dotenv import load_dotenv
import datetime
import os

load_dotenv()

class Token:
    def __init__(self):
        self.ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY")
        self.REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM")
        self.AT_EXPIRE_MINUTES = int(os.getenv("AT_EXPIRE_MINUTES"))
        self.RT_EXPIRE_MINUTES = int(os.getenv("RT_EXPIRE_MINUTES"))
    
    def create_access_token(self,
                            data:dict,
                            expire_delta:datetime.timedelta=None):
        to_encode = data.copy()
        
        if expire_delta:
            expire = datetime.datetime.now() + expire_delta
        else:
            expire = datetime.datetime.now() + datetime.timedelta(minutes=self.AT_EXPIRE_MINUTES)
        
        to_encode.update({"exp":int(expire.timestamp())})
        return jwt.encode(to_encode, self.ACCESS_SECRET_KEY, algorithm=self.ALGORITHM)
    
    def create_refresh_token(self,
                             data:dict):
        to_encode = data.copy()
        expire = datetime.datetime.now() + datetime.timedelta(minutes=self.RT_EXPIRE_MINUTES)
        to_encode.update({"exp":expire})
        return jwt.encode(to_encode, self.REFRESH_SECRET_KEY, algorithm=self.ALGORITHM)
    
    def verify_token(self, token:str, is_refresh:bool=False):
        try:
            secret_key = self.REFRESH_SECRET_KEY if is_refresh else self.ACCESS_SECRET_KEY
            payload = jwt.decode(token, secret_key, algorithms=[self.ALGORITHM])
            return payload
        except JWTError as je:
            raise je
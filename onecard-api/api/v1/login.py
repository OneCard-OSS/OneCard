from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from services.init_login import init_login

login_router = APIRouter(prefix="/api/v1")

@login_router.post("/login")
def login(emp_no:str,
          client_id:str=Query(...),
          redirect_uri:str=Query(...),
          db:Session=Depends(get_db)):
    
    return init_login(emp_no=emp_no, 
                      client_id=client_id,
                      redirect_uri=redirect_uri,
                      db=db)

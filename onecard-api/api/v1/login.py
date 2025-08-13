from fastapi import APIRouter, Query, Form, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from services.init_login import init_login

login_router = APIRouter(prefix="/api/v1")
templates = Jinja2Templates(directory="templates")

@login_router.get("/login")
def get_login_page(request:Request,
                   client_id:str=Query(...),
                   redirect_uri:str=Query(...)):
      return templates.TemplateResponse(
            "login.html",
            {"request" : request, "client_id":client_id, "redirect_uri":redirect_uri}
      )


@login_router.post("/login")
async def login(emp_no:str=Form(...),
          client_id:str=Form(...),
          redirect_uri:str=Form(...),
          db:Session=Depends(get_db)):
    
    return await init_login(emp_no=emp_no, 
                      client_id=client_id,
                      redirect_uri=redirect_uri,
                      db=db)

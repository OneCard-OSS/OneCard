from fastapi import APIRouter, status,Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.database import get_db
from crud.service.get_service import get_paginated_services

admin_router = APIRouter(prefix="/admin", tags=["Admin Pages"])
templates = Jinja2Templates(directory="templates")

@admin_router.get("/", response_class=HTMLResponse)
async def admin_root(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url="/admin/services", status_code=status.HTTP_302_FOUND)

@admin_router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})

@admin_router.get("/services", response_class=HTMLResponse)
async def get_services_page(request: Request,
                            db:Session=Depends(get_db),
                            page:int = Query(1,ge=1)):
    page_size = 10
    paginated_data = get_paginated_services(db=db, page=page, page_size=page_size)
    return templates.TemplateResponse("admin/services.html", {
        "request": request,
        "services": paginated_data["services"],
        "total_pages": paginated_data["total_pages"],
        "current_page": paginated_data["current_page"],
        "active_tab": "services"
    })

@admin_router.get("/logs", response_class=HTMLResponse)
async def get_logs_page(request: Request):
    return templates.TemplateResponse("admin/logs.html", {
        "request": request,
        "active_tab": "logs"
    })

@admin_router.get("/permissions", response_class=HTMLResponse)
async def get_permissions_page(request: Request):
    return templates.TemplateResponse("admin/permissions.html", {
        "request": request,
        "active_tab": "permissions"
    })
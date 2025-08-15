from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from utils.current_user import current_user_info
from schemas.permission import PermissionRequest,DeptPermissionRequest
from crud.permission.emp_perm import block_employee_from_service, unblock_employee_from_service
from crud.permission.dept_perm import block_department_from_service, unblock_department_from_service

perm_router = APIRouter(prefix="/api", tags=["Service Permission Control"])

@perm_router.post("/block/employee")
def block_permission_employee(request:PermissionRequest, 
                              db:Session=Depends(get_db),
                              current_user=Depends(current_user_info)):
    try:
        block_employee_from_service(client_id=request.client_id,
                                    emp_no=request.emp_no,
                                    db=db,
                                    current_user=current_user)
        return {"message" : "Permission Blocked successfully"}
    except PermissionError as pe:
        raise HTTPException(status_code=404, detail=str(pe))
    except HTTPException as he:
        raise he

@perm_router.post("/unblock/employee")
def unblock_permission_employee(request:PermissionRequest,
                              db:Session=Depends(get_db),
                              current_user=Depends(current_user_info)):
    try:
        unblock_employee_from_service(client_id=request.client_id,
                                      emp_no=request.emp_no,
                                      db=db,
                                      current_user=current_user)
        
        return {"message" : "Permission Unblocked Successfully"}
    except PermissionError as pe:
        raise HTTPException(status_code=404, detail=str(pe))
    except HTTPException as he:
        raise he

@perm_router.post("/block/dept")
def block_permission_department(request: DeptPermissionRequest,
                                db:Session=Depends(get_db),
                                current_user=Depends(current_user_info)):
    try:
        block_department_from_service(client_id=request.client_id,
                                      department_name=request.dept,
                                      db=db,
                                      current_user=current_user)
        return {"message" : "Permission Blcoked Successfully"}
    except PermissionError as pe:
        raise HTTPException(status_code=404, detail=str(pe))
    except HTTPException as he:
        raise he
    
@perm_router.post("/unblock/dept")
def unblock_permission_department(request: DeptPermissionRequest,
                                db:Session=Depends(get_db),
                                current_user=Depends(current_user_info)):
    try:
        unblock_department_from_service(client_id=request.client_id,
                                        department_name=request.dept,
                                        db=db,
                                        current_user=current_user)
        return {"message" : "Permission Unblocked Successfully"}
    except PermissionError as pe:
        raise HTTPException(status_code=404, detail=str(pe))
    except HTTPException as he:
        raise he
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.employee import Employee
from models.service import Services

def block_employee_from_service(client_id:str,
                                emp_no:str,
                                db:Session,
                                current_user:dict)->Services:
    """
    Block access to specific services by specific employee
    Args:
    - service_id: 
    - emp_no:
    - db:
    - current_user:
    Returns:
    - 
    """
    service = db.query(Services).filter(Services.client_id == client_id).first()
    if not service:
        raise PermissionError(f"Service with client id {client_id} not found.")
        
    employee = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    if not employee:
        raise PermissionError(f"Employee with emp_no {emp_no} not found.")
    
    # Check if it's already on block list to avoid adding duplicates
    if employee not in service.employees:
        service.employees.append(employee)
        db.commit()
        db.refresh(service)
    
    return service

def unblock_employee_from_service(client_id:str,
                                  emp_no:str,
                                  db:Session,
                                  current_user:str)->Services:
    """
    Unblock access for specific employees to specific services
    """
    service = db.query(Services).filter(Services.client_id == client_id).first()
    if not service:
        raise PermissionError(f"Service with id {client_id} not found.")
        
    employee = db.query(Employee).filter(Employee.emp_no == emp_no).first()
    if not employee:
        raise PermissionError(f"Employee with emp_no {emp_no} not found.")
    
    # Try removing only if it's on permission block list
    if employee in service.employees:
        service.employees.remove(employee)
        db.commit()
        db.refresh(service)
    
    return service
        
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.employee import Employee
from models.service import Services

def block_department_from_service(client_id: str, 
                                  department_name: str,
                                  db: Session,
                                  current_user:dict)->Services:
    """
    Block access to a specific service for all employees in a specific department
    """
    
    service = db.query(Services).filter(Services.client_id == client_id).first()
    if not service:
        raise PermissionError(f"Service with id {client_id} not found.")
    
    employees_in_dept = db.query(Employee).filter(Employee.department == department_name).all()
    if not employees_in_dept:
        raise PermissionError(f"No employees found in department '{department_name}'.")

    for employee in employees_in_dept:
        if employee not in service.employees:
            service.employees.append(employee)
            
    db.commit()
    db.refresh(service)
    print(f"Success: Blocked {len(employees_in_dept)} employees from department '{department_name}' for service '{service.name}'.")
    
    return service

def unblock_department_from_service(client_id:str, 
                                    department_name: str,
                                    db: Session,
                                    current_user:dict)->Services:
    """
    Unblock access for all employees in a specific department to a specific service
    """
    
    service = db.query(Services).filter(Services.client_id == client_id).first()
    if not service:
        raise PermissionError(f"Service with id {client_id} not found.")

    employees_in_dept = db.query(Employee).filter(Employee.department == department_name).all()
    if not employees_in_dept:
        raise PermissionError(f"No employees found in department '{department_name}'.")

    for employee in employees_in_dept:
        if employee in service.employees:
            service.employees.remove(employee)
            
    db.commit()
    db.refresh(service)
    print(f"Success: Unblocked employees from department '{department_name}' for service '{service.name}'.")
    
    return service
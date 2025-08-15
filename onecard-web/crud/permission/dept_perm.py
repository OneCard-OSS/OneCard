from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.employee import Employee
from models.service import Services
from models.permission import permission_table

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

    emp_no_in_dept = [emp.emp_no for emp in employees_in_dept]
    
    if emp_no_in_dept:
        # First, check if have permission to delete at least one
        permission = db.query(permission_table).filter(
            permission_table.c.service_id == service.id,
            permission_table.c.emp_no._in_(emp_no_in_dept)
        ).count()
        if permission == 0:
            raise PermissionError(
                f"No blocked employees found in department:{department_name}"
            )
        perm = permission_table.delete().where(
            permission_table.c.service_id == service.id,
            permission_table.c.emp_no.in_(emp_no_in_dept)
        ) 
        result = db.execute(perm)
        db.commit()
        print(f"Success: Unblocked employees from department '{department_name}' for service '{service.name}'.")
    else:
        print(f"Info: No employees to unblock in department '{department_name}'.")         
    db.refresh(service)
    
    return service
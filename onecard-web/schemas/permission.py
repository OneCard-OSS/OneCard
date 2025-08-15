from pydantic import BaseModel

class PermissionRequest(BaseModel):
    client_id:str
    emp_no:str

class DeptPermissionRequest(BaseModel):
    client_id:str
    dept:str    
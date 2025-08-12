from pydantic import BaseModel

class InitLoginRequest(BaseModel):
    emp_no:str
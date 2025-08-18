from pydantic import BaseModel
from typing import Optional

class ManageCard(BaseModel):
    emp_no:str
    pubkey:str
    existing:Optional[bool]=False
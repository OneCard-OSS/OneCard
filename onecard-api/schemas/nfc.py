from pydantic import BaseModel, Field
from typing import Optional

class NfcStatusResponse(BaseModel):
    status:str = Field(..., description="Authentication Attempt Status(pending, success, faield, expired)")
    s_id:Optional[str] = Field(..., description="session id issued upon success")
    error:Optional[str] = Field(None, description="Error Code when an error occurs")
    error_description:Optional[str] = Field(None, description="Description when an error occurs")
from pydantic import BaseModel, field_validator
from datetime import date
from typing import Optional
import re

# Join User Data Validation
class JoinUser(BaseModel):
    user_id : str
    user_password : str
    user_name : str
    
    @field_validator("user_id")
    def validate_user_id(cls, value):
        """
        user_id는 8~16자리이며, 영문과 숫자 조합만 허용 (기호는 불가)
        """
        pattern = re.compile(r"^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]{8,16}$")
        if not pattern.match(value):
            raise ValueError("user_id : length 8~16, using english and number, no symbol")
        return value

    @field_validator("user_password")
    def validate_user_password(cls, value):
        """
        user_password는 8~16자리이며, 영문, 숫자, 기호 조합이어야 함
        """
        pattern = re.compile(r"^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>])[a-zA-Z\d!@#$%^&*(),.?\":{}|<>]{8,16}$")
        if not pattern.match(value):
            raise ValueError("user_password : length 8~16, using english and number, must use symbol at least one")
        return value
    
    
    @field_validator("user_name")
    def validate_user_name(cls, value):
        """
        user_name은 한글 이름으로 자음만 포함되지 않도록 검증
        """
        pattern = re.compile(r"^[가-힣]{2,}$")  # 최소 2글자 이상의 한글 이름만 허용
        if not pattern.match(value):
            raise ValueError("user_name : must be a valid Korean name (at least 2 characters)")
        
        # 한글 이름에서 자음만 들어가는 경우를 막기 위한 체크 (모음이 있는지 확인)
        for char in value:
            if ord(char) in range(0x3131, 0x314F):  # 자음 범위
                raise ValueError("user_name : cannot contain only consonants (must have vowels)")
        
        return value
        
    class Config:
        from_attributes = True
        
class UserOut(BaseModel):
    user_id:str
    user_name:str
    message: str
    
class LoginRequest(BaseModel):
    user_id:str
    user_password:str
from sqlalchemy import Column, String, Date
from core.database import Base

"""
This schema is dummy schema 
"""
class Employee(Base):
    __tablename__ = "employee"
    
    emp_no = Column(String(16), primary_key=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone_num = Column(String, nullable=False)
    position = Column(String, nullable=False)
    department = Column(String, nullable=False)
    birth = Column(Date, nullable=False)
    email = Column(String, nullable=False)
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from core.database import Base

class Employee(Base):
    __tablename__ = "employee"
    
    emp_no = Column(String(16), primary_key=True, unique=True, nullable=False)
    
    pubkeys = relationship("Pubkey", back_populates="employee", cascade="all, delete")
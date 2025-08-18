from sqlalchemy import Column, String, Date
from sqlalchemy.orm import relationship
from core.database import Base
from models.permission import permission_table

class Employee(Base):
    __tablename__ = "employee"
    
    emp_no = Column(String(16), primary_key=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone_num = Column(String, nullable=False)
    position = Column(String, nullable=False)
    department = Column(String, nullable=False)
    birth = Column(Date, nullable=False)
    email = Column(String, nullable=False)
    
    pubkeys = relationship("Pubkey", back_populates="employee", cascade="all, delete")
    
    services = relationship(
        "Services",
        secondary=permission_table,
        back_populates="employees"
    )
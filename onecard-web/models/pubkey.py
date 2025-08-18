from sqlalchemy import Column, String, TIMESTAMP, text, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class Pubkey(Base):
    __tablename__ = 'pubkey'
    
    pubkey = Column(String, primary_key=True)
    emp_no = Column(
        String(16), 
        ForeignKey('employee.emp_no', ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))

    employee = relationship("Employee", back_populates="pubkeys")
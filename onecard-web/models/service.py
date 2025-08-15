from sqlalchemy import Column, String, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP
from core.database import Base
from models.permission import permission_table

class Services(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, autoincrement=True)  # serial4
    client_id = Column(String, unique=True, nullable=False)
    client_secret = Column(String, unique=True, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text('now()'))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    owner = relationship('Users', back_populates='services')
    redirect_uris = relationship("RedirectUris", back_populates="service", cascade="all, delete-orphan")
    employees= relationship(
        "Employee",
        secondary=permission_table,
        back_populates='services'
    )
    
class RedirectUris(Base):
    __tablename__ = "redirect_uris"
    id = Column(Integer, primary_key=True, autoincrement=True) # serial4
    client_id = Column(String, ForeignKey('services.client_id', ondelete='CASCADE'), nullable=False)
    uris = Column(Text, nullable=False)
    
    service = relationship("Services", back_populates="redirect_uris", passive_deletes=True)
    
    
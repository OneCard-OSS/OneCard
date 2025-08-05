from sqlalchemy import Column, String, text
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base

class Users(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(String, unique=True, nullable=False)
    user_password = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    signup_date = Column(TIMESTAMP, nullable=False, server_default=text('now()'))
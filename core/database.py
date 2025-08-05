import os
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
# SQLAlchemy Engine Creation
try:
    engine = create_engine(DATABASE_URL)
except exc.SQLAlchemyError as se:
    raise se # logging


SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

Base = declarative_base()

# Database Connection Pooling Method
# Transaction Manage
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except exc.SQLAlchemyError as se:
        db.rollback()
        raise se
    finally:
        db.close()
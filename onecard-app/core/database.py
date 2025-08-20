from sqlalchemy import create_engine, exc
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    engine = create_engine(DATABASE_URL)
except exc.SQLAlchemyError as se:
    raise se

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

Base = declarative_base()

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
        
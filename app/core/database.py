from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
load_dotenv(".env")
# Using SQLite for now (file stored locally)
#SQLALCHEMY_DATABASE_URL = "sqlite:///./sentinel.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=20,  # Limit number of persistent connections
        max_overflow=5,  # Allow a few extra temporary ones
        pool_timeout=30,  # Wait time for a connection
        pool_recycle=1800  # Recycle connections every 30 minutes
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
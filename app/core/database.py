from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Using SQLite for now (file stored locally)
SQLALCHEMY_DATABASE_URL = "sqlite:///./sentinel.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
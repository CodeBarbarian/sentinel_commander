# app/core/bootstrap.py
from sqlalchemy.orm import Session
from app.models.source import Source
from app.core.database import SessionLocal
import uuid
import secrets
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from passlib.hash import bcrypt
import logging


def generate_api_key() -> str:
    """Generate a secure 40-character hex token."""
    return secrets.token_hex(20)  # 40 characters

def ensure_internal_source():
    logger = logging.getLogger(__name__)

    db: Session = SessionLocal()
    existing = db.query(Source).filter(Source.name == "Default API Key").first()

    if not existing:
        internal = Source(
            name="Default API Key",
            display_name="Default API Key",
            api_key=generate_api_key(),
            guid=str(uuid.uuid4()),
            is_active=True,
            is_protected=True
        )
        db.add(internal)
        db.commit()
        logging.info(f"Default source created. API Key: {internal.api_key}")
    else:
        logging.info("Default source already exists.")
    db.close()

def init_data():
    logger = logging.getLogger(__name__)
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@sentinel.local").first()
        if existing:
            logging.info("[+] Admin user already exists — skipping bootstrap.")
            return

        admin = User(
            username="admin",
            full_name="Default Admin",
            email="admin@sentinel.local",
            password_hash=bcrypt.hash("ChangeMe!"),
            role="admin",
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        db.commit()
        logger.info("[+] Default admin user created (username: admin, password: ChangeMe!)")
    except Exception as e:
        db.rollback()
        logger.error(f"[!] Bootstrap error: {e}")
    finally:
        db.close()

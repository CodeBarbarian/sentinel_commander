# app/core/bootstrap.py
from sqlalchemy.orm import Session
from app.models.source import Source
from app.core.database import SessionLocal
import uuid
import secrets

def generate_api_key() -> str:
    """Generate a secure 40-character hex token."""
    return secrets.token_hex(20)  # 40 characters

def ensure_internal_source():
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
        print(f"[+] Internal testing source created. API Key: {internal.api_key}")
    else:
        print("[✓] Internal testing source already exists.")
    db.close()

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from passlib.hash import bcrypt

def init_data():
    db: Session = SessionLocal()

    # Check if any users exist
    user_exists = db.query(User).first()
    if user_exists:
        print("[+] Initial data already exists — skipping bootstrap.")
        db.close()
        return

    # Create default admin user
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
    print("[+] Default admin user created (username: admin, password: ChangeMe123!)")
    db.close()

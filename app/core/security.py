# app/core/security.py

import os
from fastapi import Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.source import Source

# Secure API key validation for Source-authenticated routes (e.g., alerts)
def get_api_key(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> Source:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization.split(" ")[1]
    source = db.query(Source).filter(Source.api_key == token, Source.is_active == True).first()

    if not source:
        raise HTTPException(status_code=403, detail="Invalid or inactive API key")
    return source

# Alternative method: retrieve current source from request context (for webhook-style access)
def get_current_source(request: Request, db: Session = Depends(get_db)) -> Source:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    source = db.query(Source).filter(Source.api_key == token, Source.is_active == True).first()
    if not source:
        raise HTTPException(status_code=403, detail="Invalid or inactive API key")

    return source

# Admin-level static API key check
ADMIN_API_KEY = os.getenv("SENTINEL_ADMIN_API_KEY", "changeme")  # Replace for production!

def require_admin_api_key(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    if token != ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin API key")

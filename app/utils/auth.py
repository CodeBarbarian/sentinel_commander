from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401)
    return user

def require_admin(request: Request):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse("/login", status_code=302)
    return user
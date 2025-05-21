import os
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils import auth
from fastapi.templating import Jinja2Templates

YAML_ROOT = {
    "alert": "app/parsers/alert",
    "triage": "app/parsers/triage"
}

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def validate_yaml_filename(file_type: str, filename: str):
    if file_type not in YAML_ROOT:
        raise HTTPException(status_code=400, detail="Invalid file type")
    if not filename.endswith(f"_{file_type}.yaml"):
        raise HTTPException(status_code=400, detail="Invalid file suffix")
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return os.path.join(YAML_ROOT[file_type], filename)


@router.get("/settings/yaml", response_class=HTMLResponse)
def yaml_editor_home(request: Request, user=Depends(auth.get_current_user)):
    # Get all YAML files grouped by type
    file_list = {"alert": [], "triage": []}
    for file_type, folder in YAML_ROOT.items():
        if os.path.exists(folder):
            file_list[file_type] = sorted([
                f for f in os.listdir(folder)
                if f.endswith(f"_{file_type}.yaml")
            ])
    return templates.TemplateResponse("settings/yaml_editor.html", {
        "request": request,
        "files": file_list
    })


@router.get("/settings/yaml/load")
def load_yaml_file(file_type: str, filename: str, user=Depends(auth.get_current_user)):
    full_path = validate_yaml_filename(file_type, filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    return JSONResponse(content={"content": content})


@router.post("/settings/yaml/save")
async def save_yaml_file(
    request: Request,
    user=Depends(auth.get_current_user)
):
    form = await request.form()
    file_type = form.get("file_type")
    filename = form.get("filename")
    content = form.get("content")

    full_path = validate_yaml_filename(file_type, filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.replace("\r\n", "\n"))

    return RedirectResponse(url="/web/v1/settings/yaml", status_code=303)

@router.post("/settings/yaml/delete")
def delete_yaml_file(
    file_type: str = Form(...),
    filename: str = Form(...),
    user=Depends(auth.get_current_user)
):
    full_path = validate_yaml_filename(file_type, filename)
    if os.path.exists(full_path):
        os.remove(full_path)
    return RedirectResponse(url="/web/v1/settings/yaml", status_code=303)

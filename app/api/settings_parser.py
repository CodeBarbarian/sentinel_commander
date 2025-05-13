from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse
from fastapi import Depends
from typing import List
import os
import yaml
from app.core.security import require_admin_api_key
router = APIRouter(dependencies=[Depends(require_admin_api_key)])
PARSERS_DIR = "app/parsers"

# Ensure the directory exists
os.makedirs(PARSERS_DIR, exist_ok=True)

@router.get("/settings/parsers", response_model=List[dict])
def list_parsers():
    parsers = []
    for file in os.listdir(PARSERS_DIR):
        if file.endswith(".yaml"):
            with open(os.path.join(PARSERS_DIR, file), "r") as f:
                data = yaml.safe_load(f)
                parsers.append({
                    "name": data.get("parser_name", file.replace(".yaml", "")),
                    "filename": file
                })
    return parsers

@router.get("/settings/parsers/{name}", response_class=PlainTextResponse)
def get_parser(name: str):
    path = os.path.join(PARSERS_DIR, f"{name}.yaml")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Parser not found")
    with open(path, "r") as f:
        return f.read()

@router.post("/settings/parsers")
def upload_parser(file: UploadFile = File(...)):
    if not file.filename.endswith(".yaml"):
        raise HTTPException(status_code=400, detail="Only .yaml files allowed")
    content = file.file.read().decode("utf-8")
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        raise HTTPException(status_code=400, detail="Invalid YAML format")
    parser_name = data.get("parser_name")
    if not parser_name:
        raise HTTPException(status_code=400, detail="Missing 'parser_name' field in YAML")
    path = os.path.join(PARSERS_DIR, f"{parser_name}.yaml")
    with open(path, "w") as f:
        f.write(content)
    return {"status": "ok", "message": f"Parser saved as {parser_name}.yaml"}

@router.delete("/settings/parsers/{name}")
def delete_parser(name: str):
    path = os.path.join(PARSERS_DIR, f"{name}.yaml")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Parser not found")
    os.remove(path)
    return {"status": "deleted", "parser": name}

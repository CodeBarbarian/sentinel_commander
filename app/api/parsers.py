import os
import shutil
import yaml
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.utils.parser.engine import run_custom_parser

router = APIRouter()
DEFAULT_PARSER_DIR = "app/parsers/default"
PARSER_DIR = "app/parsers/custom"
BACKUP_DIR = "app/parsers/backups"
os.makedirs(DEFAULT_PARSER_DIR, exist_ok=True)
os.makedirs(PARSER_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)


# ──────────────────────────────────────────
# Sandbox Parser Testing
# ──────────────────────────────────────────
@router.post("/parsers/sandbox")
async def parse_alert_sandbox(
    parser_file: UploadFile = File(...),
    alert_json: str = Form(...)
):
    try:
        parser_yaml = yaml.safe_load(await parser_file.read())
        alert = json.loads(alert_json)
        parsed_result = run_custom_parser(parser_yaml, alert)
        return {"success": True, "parsed": parsed_result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────
# Create New Parser (Named)
# ──────────────────────────────────────────
@router.post("/parsers")
async def add_parser(body: dict):
    yaml_content = body.get("yaml")
    if not yaml_content:
        raise HTTPException(status_code=400, detail="YAML content missing.")

    try:
        parsed = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    name = parsed.get("name", "unnamed_parser").replace(" ", "_").lower()
    filename = f"{name}.yaml"
    path = os.path.join(PARSER_DIR, filename)

    if os.path.exists(path):
        raise HTTPException(status_code=409, detail="Parser with this name already exists.")

    with open(path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    log_action("created", filename)
    return {"success": True, "filename": filename}


# ──────────────────────────────────────────
# List Parsers
# ──────────────────────────────────────────
@router.get("/parsers")
async def list_parsers():
    output = []

    # Load default parsers
    for f in os.listdir(DEFAULT_PARSER_DIR):
        if f.endswith(".yaml"):
            try:
                with open(os.path.join(DEFAULT_PARSER_DIR, f), "r", encoding="utf-8") as file:
                    content = yaml.safe_load(file)
                    output.append({
                        "name": content.get("name", "Unnamed"),
                        "filename": f,
                        "location": "default"
                    })
            except Exception:
                output.append({
                    "name": "Invalid YAML",
                    "filename": f,
                    "location": "default"
                })

    # Load custom parsers
    for f in os.listdir(PARSER_DIR):
        if f.endswith(".yaml"):
            try:
                with open(os.path.join(PARSER_DIR, f), "r", encoding="utf-8") as file:
                    content = yaml.safe_load(file)
                    output.append({
                        "name": content.get("name", "Unnamed"),
                        "filename": f,
                        "location": "custom"
                    })
            except Exception:
                output.append({
                    "name": "Invalid YAML",
                    "filename": f,
                    "location": "custom"
                })

    return output


# ──────────────────────────────────────────
# Get Raw Parser YAML
# ──────────────────────────────────────────
@router.get("/parsers/{filename}", response_class=PlainTextResponse)
async def get_parser_file(filename: str):
    path = os.path.join(PARSER_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Parser not found")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ──────────────────────────────────────────
# Update/Overwrite Parser
# ──────────────────────────────────────────
@router.put("/parsers/{filename}")
async def update_parser_file(filename: str, body: Request):
    path = os.path.join(PARSER_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Parser not found")

    try:
        content = await body.body()
        yaml.safe_load(content)  # Validate first

        # Backup original
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        shutil.copy(path, os.path.join(BACKUP_DIR, f"{filename}.{timestamp}.bak"))

        # Save new version
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.decode("utf-8"))

        log_action("edited", filename)
        return {"success": True}
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────
# Delete Parser
# ──────────────────────────────────────────
@router.delete("/parsers/{filename}")
async def delete_parser(filename: str):
    path = os.path.join(PARSER_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Parser not found")

    shutil.move(path, os.path.join(BACKUP_DIR, f"{filename}.deleted.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"))
    log_action("deleted", filename)
    return {"success": True}


# ──────────────────────────────────────────
# Simple Audit Log Function
# ──────────────────────────────────────────
def log_action(action: str, filename: str):
    log_path = os.path.join(PARSER_DIR, "parser.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.utcnow().isoformat()}] {action.upper()}: {filename}\n")
@router.get("/parsers/view/{location}/{filename}", response_class=PlainTextResponse)
async def get_parser_any(location: str, filename: str):
    if location == "custom":
        path = os.path.join(PARSER_DIR, filename)
    elif location == "default":
        path = os.path.join(DEFAULT_PARSER_DIR, filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid location")

    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Parser not found")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@router.put("/parsers/view/{location}/{filename}")
async def update_parser_any(location: str, filename: str, body: Request):
    if location == "custom":
        path = os.path.join(PARSER_DIR, filename)
    elif location == "default":
        path = os.path.join(DEFAULT_PARSER_DIR, filename)
    else:
        raise HTTPException(status_code=400, detail="Invalid location")

    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Parser not found")

    try:
        content = await body.body()
        yaml.safe_load(content)

        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        shutil.copy(path, os.path.join(BACKUP_DIR, f"{filename}.{timestamp}.bak"))

        with open(path, "w", encoding="utf-8") as f:
            f.write(content.decode("utf-8"))

        log_action(f"edited ({location})", filename)
        return {"success": True}
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

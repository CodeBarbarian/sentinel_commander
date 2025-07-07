# app/utils/parser/general_parser_engine.py

import yaml
from pathlib import Path

from sqlalchemy.orm import Session

from app.utils.parser.engine import run_custom_parser

PARSER_BASE_DIR = Path("app/parsers")

def load_yaml_file(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def run_parser_for_type(parser_type: str, source_payload: dict, db: Session = None):
    parser_dir = PARSER_BASE_DIR / parser_type
    result = {
        "matched": False,
        "parser_type": parser_type,
        "parser_name": "none",
        "mapped_fields": {},
        "tags": [],
        "enrichment": {},
        "raw_config": {},
        "error": None
    }

    try:
        default_result = {}
        matches = []

        # Load default first, if it exists
        default_path = parser_dir / "default.yaml"
        if default_path.exists():
            default_yaml = load_yaml_file(default_path)
            default_result = run_custom_parser(default_yaml, source_payload, db)
            result.update({
                "mapped_fields": default_result.get("mapped_fields", {}),
                "tags": default_result.get("tags", []),
                "enrichment": default_result.get("enrichment", {}),
                "parser_name": default_result.get("parser_name", "default"),
                "matched": default_result.get("matched", False),
                "raw_config": default_yaml
            })

        # Find all matching override parsers
        for parser_path in parser_dir.glob("*.yaml"):
            if parser_path.name == "default.yaml":
                continue

            parser_yaml = load_yaml_file(parser_path)
            parser_result = run_custom_parser(parser_yaml, source_payload, db)

            if parser_result.get("matched"):
                matches.append({
                    "priority": parser_yaml.get("priority", 0),
                    "parser_result": parser_result,
                    "raw_config": parser_yaml
                })

        if matches:
            # Pick the match with the highest priority
            best_match = sorted(matches, key=lambda x: x["priority"], reverse=True)[0]

            result.update({
                "matched": True,
                "mapped_fields": best_match["parser_result"].get("mapped_fields", {}),
                "tags": list(set(result["tags"] + best_match["parser_result"].get("tags", []))),
                "enrichment": best_match["parser_result"].get("enrichment", {}),
                "parser_name": best_match["parser_result"].get("parser_name"),
                "raw_config": best_match["raw_config"]
            })

    except Exception as e:
        result["error"] = str(e)

    return result


# app/utils/parser/general_parser_engine.py

import yaml
from pathlib import Path
from app.utils.parser.engine import run_custom_parser

PARSER_BASE_DIR = Path("app/parsers")

def load_yaml_file(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def run_parser_for_type(parser_type: str, source_payload: dict):
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
        # Load and apply default first
        default_path = parser_dir / "default.yaml"
        if default_path.exists():
            default_yaml = load_yaml_file(default_path)
            default_result = run_custom_parser(default_yaml, source_payload)
            result.update({
                "mapped_fields": default_result.get("mapped_fields", {}),
                "tags": default_result.get("tags", []),
                "enrichment": default_result.get("enrichment", {}),
                "parser_name": default_result.get("parser_name", "default"),
                "matched": default_result.get("matched", False),
                "raw_config": default_yaml
            })

        # Look for matching override parser
        for parser_path in parser_dir.glob("*.yaml"):
            if parser_path.name == "default.yaml":
                continue

            parser_yaml = load_yaml_file(parser_path)
            parser_result = run_custom_parser(parser_yaml, source_payload)

            if parser_result.get("matched"):
                result.update({
                    "matched": True,
                    "mapped_fields": parser_result.get("mapped_fields", {}),
                    "tags": list(set(result["tags"] + parser_result.get("tags", []))),
                    "enrichment": parser_result.get("enrichment", {}),
                    "parser_name": parser_result.get("parser_name"),
                    "raw_config": parser_yaml
                })
                break

    except Exception as e:
        result["error"] = str(e)

    return result

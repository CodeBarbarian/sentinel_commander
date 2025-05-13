from pathlib import Path
import yaml
from app.utils.parser.engine import run_custom_parser

PARSER_DIR = Path("app/parsers")

def load_yaml_file(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def run_combined_parser(source_payload: dict):
    try:
        # Step 1: Load and run the default parser
        default_path = PARSER_DIR / "default/default_parser.yaml"
        default_yaml = load_yaml_file(default_path)

        parsed = run_custom_parser(default_yaml, source_payload)

        # Step 2: Check and override with matching custom parser
        for parser_path in PARSER_DIR.glob("*.yaml"):
            if parser_path.name == "default_parser.yaml":
                continue

            custom_yaml = load_yaml_file(parser_path)
            result = run_custom_parser(custom_yaml, source_payload)

            if result.get("matched"):
                parsed["mapped_fields"].update(result.get("mapped_fields", {}))
                parsed["tags"] = list(set(parsed["tags"] + result.get("tags", [])))
                parsed["enrichment"].update(result.get("enrichment", {}))
                parsed["parser_name"] = result.get("parser_name")
                break  # stop after first match

        return parsed

    except Exception as e:
        return {
            "matched": False,
            "mapped_fields": {},
            "tags": [],
            "enrichment": {},
            "parser_name": "none",
            "error": str(e)
        }

# app/utils/parser/compat_parser_runner.py

from app.utils.parser.general_parser_engine import run_parser_for_type

def run_combined_parser(source_payload: dict):
    result = run_parser_for_type("alert", source_payload)
    return {
        "matched": result["matched"],
        "mapped_fields": result["mapped_fields"],
        "tags": result["tags"],
        "enrichment": result["enrichment"],
        "parser_name": result["parser_name"]
    }
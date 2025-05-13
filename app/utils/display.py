import json
from app.utils.parser.runner import run_combined_parser


def prepare_alert_for_display(alert_obj):
    """
    Parses the alert using its source_payload (if available),
    and attaches parsed_fields, parser_tags, layout, etc.
    """
    try:
        source_payload = json.loads(alert_obj.source_payload) if alert_obj.source_payload else alert_obj.__dict__
    except Exception:
        source_payload = alert_obj.__dict__

    try:
        result = run_combined_parser(source_payload)
        print("[DEBUG] Parser result:", json.dumps(result, indent=2))
        if result.get("matched"):
            alert_obj.parsed_fields = result.get("mapped_fields", {})
            alert_obj.parser_tags = result.get("tags", [])
            alert_obj.parser_enrichment = result.get("enrichment", {})
            alert_obj.parser_layout = result.get("display", {}).get("always_show", [])
            alert_obj.parser_name = result.get("parser_name")
            alert_obj.parser_styles = result.get("style_map", {})  # style_map will include things like severity color
    except Exception as e:
        alert_obj.parsed_fields = {"error": str(e)}
        alert_obj.parser_tags = []
        alert_obj.parser_enrichment = {}
        alert_obj.parser_layout = []
        alert_obj.parser_name = None
        alert_obj.parser_styles = {}

    return alert_obj

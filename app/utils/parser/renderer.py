import yaml
import json
from pathlib import Path

ALERT_UI_CONFIG_PATH = Path("app/parsers/system/alert_settings.yaml")
ALERT_DETAIL_CONFIG_PATH = Path("app/parsers/system/alert_detail_settings.yaml")

def load_yaml_config(path: Path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_alert_ui_config():
    return load_yaml_config(ALERT_UI_CONFIG_PATH)

def load_alert_detail_config():
    return load_yaml_config(ALERT_DETAIL_CONFIG_PATH)

def render_alert_card_fields(alert_data, parsed_fields=None, config=None):
    if not config:
        config = load_alert_ui_config()

    layout = config.get("display", {})
    fields = layout.get("always_show", [])

    combined_data = dict(alert_data)
    if parsed_fields:
        combined_data.update(parsed_fields)

    rendered = []
    for field_conf in fields:
        key = field_conf.get("field")
        label = field_conf.get("label", key.title())
        style = field_conf.get("style", "default")
        no_label = field_conf.get("no_label", False)
        raw_value = combined_data.get(key, "-")
        color = None

        if isinstance(raw_value, list):
            value = ", ".join(str(item) for item in raw_value)
        elif raw_value is None:
            value = "-"
        else:
            value = str(raw_value)

        translate_map = field_conf.get("translate", {})
        # Normalize translate map for robust matching
        translate_map = {str(k).lower(): v for k, v in translate_map.items()}

        if str(value).lower() in translate_map:
            value = translate_map[str(value).lower()]

        if style == "severity_level":
            try:
                sev_int = int(raw_value)
                translated = translate_map.get(str(sev_int))
                if translated:
                    value = translated
            except Exception:
                value = "unknown"
            style = "severity_color"

        color_map = field_conf.get("color_map", {})
        if value.lower() in color_map:
            color = color_map[value.lower()]

        if key == "asset_tags" and value == "-":
            agent_name = combined_data.get("agent_name")
            if agent_name:
                value = agent_name

        rendered.append({
            "key": key,
            "label": label,
            "value": value,
            "style": style,
            "color": color,
            "no_label": no_label
        })
    #print(f"[RENDER DEBUG] Alert ID: {combined_data.get('id')}, Field: {key}, Raw: {raw_value}, Final: {value}, Style: {style}")

    return rendered

def render_alert_detail_fields(alert_data, parsed_fields=None, config=None, extra_context=None):
    if not config:
        config = load_alert_detail_config()

    sections = config.get("display", {}).get("sections", [])

    combined_data = dict(alert_data)
    if parsed_fields:
        combined_data.update(parsed_fields)
    if extra_context:
        combined_data.update(extra_context)

    rendered_sections = []

    for section in sections:
        section_title = section.get("title", "Untitled")
        section_style = section.get("style", "default")
        fields_conf = section.get("fields", [])
        source_key = section.get("source")

        rendered_fields = []

        # Handle dictionary sources like parsed_fields, parsed_tags, etc.
        if source_key and source_key in combined_data:
            source_data = combined_data[source_key]

            if section_style == "tag_list" and isinstance(source_data, list):
                for tag in source_data:
                    rendered_fields.append({
                        "key": tag,
                        "label": tag,
                        "value": tag,
                        "style": "tag_list",
                        "no_label": True
                    })
            elif section_style == "json":
                if isinstance(source_data, str):
                    try:
                        source_data = json.loads(source_data)
                    except Exception:
                        pass  # Use as-is if not valid JSON
                rendered_fields.append({
                    "key": source_key,
                    "label": source_key.replace("_", " ").title(),
                    "value": json.dumps(source_data, indent=2),
                    "style": "json",
                    "no_label": True
                })
            elif section_style == "auto" and isinstance(source_data, dict):
                for k, v in source_data.items():
                    val = ", ".join(v) if isinstance(v, list) else v
                    rendered_fields.append({
                        "key": k,
                        "label": k.replace("_", " ").title(),
                        "value": val,
                        "style": "default",
                        "no_label": False
                    })

            rendered_sections.append({
                "title": section_title,
                "style": section_style,
                "fields": rendered_fields
            })
            continue

        # Handle explicitly defined fields
        for field_conf in fields_conf:
            key = field_conf.get("field")
            label = field_conf.get("label", key.title())
            style = field_conf.get("style", "default")
            no_label = field_conf.get("no_label", False)
            translate_map = field_conf.get("translate", {})
            color_map = field_conf.get("color_map", {})

            raw_value = combined_data.get(key, "-")
            if isinstance(raw_value, list):
                value = ", ".join(str(item) for item in raw_value)
            elif raw_value is None:
                value = "-"
            else:
                value = str(raw_value)

            # Translate display value first
            display_value = value
            if style == "severity_level":
                try:
                    sev_int = int(raw_value)
                    display_value = translate_map.get(sev_int, "unknown")
                except Exception:
                    display_value = "unknown"
                style = "severity_color"
            else:
                display_value = translate_map.get(value) or translate_map.get(value.lower(), value)

            # Use display_value to look up color
            color = color_map.get(display_value.lower())

            rendered_fields.append({
                "key": key,
                "label": label,
                "value": display_value,
                "style": style,
                "color": color,
                "no_label": no_label
            })

        rendered_sections.append({
            "title": section_title,
            "style": section_style,
            "fields": rendered_fields
        })

    return rendered_sections

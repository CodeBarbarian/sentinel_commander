import re
from collections import OrderedDict
from app.web.modules.maxmind_module import lookup_country
def extract_from_path(data, path):
    try:
        parts = re.split(r'\.(?![^\[]*\])', path)
        for part in parts:
            match = re.match(r'([^\[\]]+)(?:\[(\d+)\])?', part)
            if not match:
                continue
            key, idx = match.groups()
            data = data.get(key)
            if idx is not None and isinstance(data, list):
                data = data[int(idx)]
        return data
    except Exception:
        return None

def evaluate_condition(data, condition_str):
    def _eval_single(condition):
        try:
            # Greater or equal
            if ">=" in condition:
                left, right = condition.split(">=", 1)
                return float(extract_from_path(data, left.strip()) or 0) >= float(right.strip())
            # Less or equal
            elif "<=" in condition:
                left, right = condition.split("<=", 1)
                return float(extract_from_path(data, left.strip()) or 0) <= float(right.strip())
            # Greater than
            elif ">" in condition:
                left, right = condition.split(">", 1)
                return float(extract_from_path(data, left.strip()) or 0) > float(right.strip())
            # Less than
            elif "<" in condition:
                left, right = condition.split("<", 1)
                return float(extract_from_path(data, left.strip()) or 0) < float(right.strip())
            # Equal
            elif "==" in condition:
                left, right = condition.split("==", 1)
                return str(extract_from_path(data, left.strip())) == right.strip().strip('"').strip("'")
            # Not equal
            elif "!=" in condition:
                left, right = condition.split("!=", 1)
                return str(extract_from_path(data, left.strip())) != right.strip().strip('"').strip("'")
            elif " not in " in condition:
                left, right = condition.split(" not in ", 1)
                val = left.strip().strip('"').strip("'")
                container = extract_from_path(data, right.strip())
                return val not in container if isinstance(container, list) else val not in str(container)
            elif " in " in condition:
                left, right = condition.split(" in ", 1)
                val = left.strip().strip('"').strip("'")
                container = extract_from_path(data, right.strip())
                return val in container if isinstance(container, list) else val in str(container)
            elif " startswith " in condition:
                left, right = condition.split(" startswith ", 1)
                val = extract_from_path(data, left.strip())
                return isinstance(val, str) and val.startswith(right.strip().strip('"').strip("'"))
            elif " endswith " in condition:
                left, right = condition.split(" endswith ", 1)
                val = extract_from_path(data, left.strip())
                return isinstance(val, str) and val.endswith(right.strip().strip('"').strip("'"))
            elif " matches " in condition:
                left, right = condition.split(" matches ", 1)
                val = extract_from_path(data, left.strip())
                pattern = right.strip().strip('"').strip("'")
                return isinstance(val, str) and re.match(pattern, val)
            return False
        except Exception:
            return False

    try:
        if " and " in condition_str:
            return all(_eval_single(part.strip()) for part in condition_str.split(" and "))
        elif " or " in condition_str:
            return any(_eval_single(part.strip()) for part in condition_str.split(" or "))
        else:
            return _eval_single(condition_str.strip())
    except Exception:
        return False

def run_custom_parser(yaml_config, alert_input):
    parsed = {
        "matched": False,
        "mapped_fields": {},
        "tags": [],
        "enrichment": {},
        "parser_name": yaml_config.get("parser_name", "unknown")
    }

    try:
        alert_source = alert_input.get("_source", alert_input)

        match_cfg = yaml_config.get("match", {})
        match_source = match_cfg.get("source")
        match_location = match_cfg.get("location")

        alert_source_val = alert_source.get("source", "").lower()
        alert_location_val = alert_source.get("location", "").lower()

        is_source_match = match_source is None or match_source.lower() == alert_source_val
        is_location_match = match_location is None or match_location.lower() == alert_location_val

        if not (is_source_match and is_location_match):
            return parsed

        parsed["matched"] = True

        field_def = yaml_config.get("fields", {})
        for field_name, field_path in field_def.items():
            if field_name == "tags":
                continue
            parsed["mapped_fields"][field_name] = extract_from_path(alert_source, field_path)

        if "tags" in field_def:
            parsed["tags"].extend(field_def["tags"])

        enrichments = yaml_config.get("enrichment", [])
        for enrich in enrichments:
            enrich_type = enrich.get("type")
            if enrich_type == "ip_lookup":
                ip_val = extract_from_path(alert_source, enrich.get("field"))
                if ip_val:
                    parsed["enrichment"]["ip_lookup"] = {
                        "ip": ip_val,
                        "info": "This is a placeholder for IP enrichment."
                    }
            elif enrich_type == "geolocation":
                ip_val = extract_from_path(alert_source, enrich.get("field"))
                if ip_val:
                    geo_info = lookup_country(ip_val)
                    parsed["enrichment"]["geolocation"] = geo_info

            elif enrich_type == "tag_if":
                condition = enrich.get("condition", "")
                tag = enrich.get("tag", "")
                if evaluate_condition(alert_source, condition):
                    parsed["tags"].append(tag)

            elif enrich_type == "set_field_if":
                condition = enrich.get("condition", "")
                field = enrich.get("field", "")
                value = enrich.get("value", "")
                if field and evaluate_condition(alert_source, condition):
                    # Prevent overwrite unless allowed
                    if field not in parsed["mapped_fields"]:
                        parsed["mapped_fields"][field] = value

        # Ensure tags are unique while preserving order
        parsed["tags"] = list(OrderedDict.fromkeys(parsed["tags"]))

        return parsed
    except Exception as e:
        raise RuntimeError(f"Parser failed: {str(e)}")

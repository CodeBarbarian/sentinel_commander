import re
from collections import OrderedDict
from sqlalchemy.orm import Session

def extract_from_path(data, path):
    try:
        parts = re.split(r'\.(?![^\[]*\])', path)
        for part in parts:
            if not isinstance(data, dict):
                return None
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

def run_custom_parser(yaml_config, alert_input, db: Session = None):
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

            elif enrich_type == "host_threat_lookup":
                field_path = enrich.get("field")
                lookup_key = enrich.get("key", "host_threat_lookup")
                value = extract_from_path(alert_source, field_path)

                if value:
                    vt_url = f"https://www.virustotal.com/gui/search/{value}"
                    talos_url = f"http://talosintelligence.com/reputation_center/lookup?search={value}"
                    abuseipdb_url = f"https://www.abuseipdb.com/check/{value}"
                    threatminer_url = f"https://www.threatminer.org/host.php?q={value}"
                    threatcrowd_url = f"http://ci-www.threatcrowd.org/ip.php?ip={value}"
                    alienvault_url = f"https://otx.alienvault.com/indicator/ip/{value}"
                    crowdsec_url = f"https://app.crowdsec.net/cti/{value}"

                    parsed["enrichment"][lookup_key] = {
                        "value": value,
                        "links": {
                            "virustotal": vt_url,
                            "talos": talos_url,
                            "abuseipdb": abuseipdb_url,
                            "threatminer": threatminer_url,
                            "threatcrowd": threatcrowd_url,
                            "alienvault": alienvault_url,
                            "crowdsec": crowdsec_url
                        }
                    }
        # Ensure tags are unique while preserving order
        parsed["tags"] = list(OrderedDict.fromkeys(parsed["tags"]))

        return parsed
    except Exception as e:
        raise RuntimeError(f"Parser failed: {str(e)}")

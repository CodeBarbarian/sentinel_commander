import yaml
from pathlib import Path
from functools import lru_cache

BASE_PATH = Path("app/parsers/system")

@lru_cache
def load_config(filename: str) -> dict:
    """Load and cache a system config YAML file by name."""
    full_path = BASE_PATH / filename
    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {filename}")
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def get_alert_card_config():
    return load_config("alert_settings.yaml")

def get_alert_detail_config():
    return load_config("alert_detail_settings.yaml")

def get_dashboard_config():
    return load_config("dashboard_settings.yaml")

def get_source_settings():
    return load_config("source_settings.yaml")

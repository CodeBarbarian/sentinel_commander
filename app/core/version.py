import requests

def get_local_version():
    try:
        with open("VERSION.md", "r") as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"

def get_remote_version():
    try:
        url = "https://raw.githubusercontent.com/codebarbarian/sentinel_commander/main/VERSION.md"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception:
        pass
    return None

def is_version_outdated():
    local = get_local_version()
    remote = get_remote_version()
    if not remote:
        return False
    return local != remote

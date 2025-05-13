#!/var/ossec/framework/python/bin/python3
# custom-sentinel.py
# Send Wazuh alerts to Sentinel Commander

# TODO: Add logging to this

import sys
import json
import requests
import uuid

# Read CLI args from ossec.conf
alert_file = sys.argv[1]
api_key = sys.argv[2]
hook_url = sys.argv[3]

# Load the Wazuh alert JSON
with open(alert_file) as f:
    alert_json = json.load(f)

# Prepare payload matching Sentinel Commander AlertCreate
payload = {
    "source": "wazuh",
    "source_ref_id": alert_json.get("id", str(uuid.uuid4())),
    "severity": alert_json.get("rule", {}).get("level", 1),
    "message": alert_json.get("rule", {}).get("description", "No description"),
    "observables": "",  # Must be a string, not a list
    "status": "new",
    "tags": f"wazuh,{alert_json.get('agent', {}).get('name', 'unknown')}",
    "source_event_time": alert_json.get("timestamp"),
    "source_payload": json.dumps(alert_json)  # Serialize dict to string
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

# Send alert to Sentinel Commander
response = requests.post(hook_url, headers=headers, json=payload, verify=False)

# Optional: print/log response for troubleshooting
if response.status_code not in (200, 201, 202):
    print(f"[-] Error sending alert: {response.status_code} - {response.text}")
else:
    print(f"[+] Alert sent: {response.status_code}")

sys.exit(0)
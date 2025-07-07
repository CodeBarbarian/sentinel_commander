import logging
import re
import requests
from sqlalchemy.orm import Session
from app.models.module import Module
from ipaddress import ip_address, AddressValueError

class VirusTotalEnrichment:
    logger = logging.getLogger("modules.virustotal")

    def __init__(self, db: Session):
        self.db = db

        module = db.query(Module).filter(Module.name == "VirusTotal", Module.is_local == False).first()
        if not module:
            self.logger.info("VirusTotal module not configured")
            self.url = None
            self.api_key = None
            return

        self.url = module.remote_url
        self.api_key = module.remote_api_key

    def detect_type(self, value: str) -> str:
        """Rudimentary check for value type"""
        try:
            ip_address(value)
            return "ip_address"
        except AddressValueError:
            pass

        if re.match(r"^[a-fA-F0-9]{32}$", value) or re.match(r"^[a-fA-F0-9]{40}$", value) or re.match(r"^[a-fA-F0-9]{64}$", value):
            return "file_hash"

        if re.match(r"^(?!:\/\/)([a-zA-Z0-9-_]+\.)+[a-zA-Z]{2,11}$", value):
            return "domain"

        if re.match(r"^https?:\/\/", value):
            return "url"

        return "unknown"

    def lookup(self, value: str) -> dict:
        if not self.url or not self.api_key:
            return {"error": "VirusTotal module is not properly configured"}

        val_type = self.detect_type(value)
        if val_type == "unknown":
            return {"error": "Could not detect type for VirusTotal lookup"}

        if val_type == "url":
            import base64
            value_id = base64.urlsafe_b64encode(value.encode()).decode().strip("=")
            endpoint = f"{self.url}/urls/{value_id}"
        elif val_type == "ip_address":
            endpoint = f"{self.url}/ip_addresses/{value}"
        elif val_type == "domain":
            endpoint = f"{self.url}/domains/{value}"
        elif val_type == "file_hash":
            endpoint = f"{self.url}/files/{value}"
        else:
            return {"error": f"Unsupported value type: {val_type}"}

        headers = {
            "x-apikey": self.api_key
        }

        try:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"VirusTotal API returned status {response.status_code}: {response.text}"}
        except Exception as e:
            self.logger.error(f"VirusTotal lookup failed for {value}: {e}")
            return {"error": str(e)}

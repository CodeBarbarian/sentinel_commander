import logging
from typing import Optional
from sqlalchemy.orm import Session
from pymisp import ExpandedPyMISP
from app.models.module import Module

logger = logging.getLogger(__name__)

class MISPEnrichment:
    def __init__(self, db: Session):
        self.db = db
        self.client = None

        # Get the remote MISP module config
        module = db.query(Module).filter(Module.name == "MISP", Module.is_local == False).first()
        if not module:
            logger.warning("⚠️ MISP remote module not found in database.")
            return

        self.url = module.remote_url
        self.api_key = module.remote_api_key

        # Check for MISP_VERIFY_CERT in local config (default: true)
        verify_cert = db.query(Module).filter(Module.name == "MISP_VERIFY_CERT", Module.is_local == True).first()
        self.verify = True  # Default to secure

        if verify_cert and verify_cert.local_key:
            self.verify = verify_cert.local_key.strip().lower() != "false"

        if not self.url or not self.api_key:
            logger.warning("⚠️ MISP remote module is missing URL or API key.")
            return

        try:
            self.client = ExpandedPyMISP(self.url, self.api_key, self.verify, debug=False)
            logger.info(f"✅ MISP client initialized (verify_cert={self.verify})")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MISP client: {e}")

    def enrich_with_misp(self, value: str) -> dict:
        if not self.client:
            return {"error": "MISP client not initialized"}

        try:
            result = self.client.search('attributes', value=value, pythonify=False)
            print("The Result is: ")
            print(result)
            # 🔍 FIX: Check if 'Attribute' is in the FIRST dict of response list
            response = result
            print("The Response is: ")
            print(response)
            if isinstance(response, dict):
                attributes = response.get("Attribute", [])
            elif isinstance(response, list) and len(response) > 0 and isinstance(response[0], dict):
                attributes = response[0].get("Attribute", [])
            else:
                attributes = []

            if not attributes:
                return {"matches": 0, "data": []}

            data = []
            for attr in attributes:
                event = attr.get("Event", {})
                data.append({
                    "attribute_id": attr.get("id"),
                    "type": attr.get("type"),
                    "category": attr.get("category"),
                    "value": attr.get("value"),
                    "to_ids": attr.get("to_ids"),
                    "tags": [tag.get("name") for tag in attr.get("Tag", [])] if isinstance(attr.get("Tag"),
                                                                                           list) else [],
                    "event": {
                        "id": event.get("id", "N/A"),
                        "info": event.get("info", "No title"),
                        "org": event.get("Orgc", {}).get("name") if isinstance(event.get("Orgc"), dict) else "Unknown",
                        "date": event.get("date", "Unknown")
                    }
                })

            return {
                "matches": len(data),
                "source": "MISP",
                "data": data
            }

        except Exception as e:
            logger.error(f"❌ MISP enrichment failed for {value}: {e}")
            return {"error": str(e)}







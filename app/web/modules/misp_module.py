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
            result = self.client.search('attributes', value=value, pythonify=True)
            if not result or not result.get("Attribute"):
                return {"matches": 0, "data": []}

            data = []
            for attr in result["Attribute"]:
                event_info = None
                try:
                    event = self.client.get_event(attr.event_id, pythonify=True)
                    event_info = {
                        "id": attr.event_id,
                        "info": getattr(event, "info", "No title"),
                        "org": getattr(event, "Orgc", {}).get("name", "Unknown") if event else "Unknown",
                        "date": getattr(event, "date", "Unknown"),
                        "tags": [t["name"] for t in event.tags] if event and event.tags else []
                    }
                except Exception:
                    event_info = {"id": attr.event_id, "info": "Unavailable", "tags": []}

                data.append({
                    "attribute_id": attr.id,
                    "type": attr.type,
                    "category": attr.category,
                    "value": attr.value,
                    "to_ids": attr.to_ids,
                    "event": event_info,
                })

            return {
                "matches": len(data),
                "source": "MISP",
                "data": data
            }

        except Exception as e:
            logger.error(f"❌ MISP enrichment failed for {value}: {e}")
            return {"error": str(e)}

import os
from urllib.parse import urlencode

import geoip2.database
import requests
import tarfile
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.module import Module
from app.utils import auth
from fastapi.responses import RedirectResponse
router = APIRouter()

# Path setup
RESOURCE_DIR = os.path.join("app", "resources")
GEOIP_DB_PATH = os.path.join(RESOURCE_DIR, "GeoLite2-Country.mmdb")
GEOIP_TAR_PATH = os.path.join(RESOURCE_DIR, "GeoLite2-Country.tar.gz")

# Initialize reader
reader = None
if os.path.exists(GEOIP_DB_PATH):
    try:
        reader = geoip2.database.Reader(GEOIP_DB_PATH)
    except Exception:
        reader = None

def lookup_country(ip_address: str):
    if reader is None:
        return {
            "ip": ip_address,
            "country": "GeoIP DB missing",
            "iso_code": "N/A",
            "provider": "GeoLite2 (Unavailable)"
        }
    try:
        response = reader.country(ip_address)
        return {
            "ip": ip_address,
            "country": response.country.name,
            "iso_code": response.country.iso_code,
            "provider": "GeoLite2"
        }
    except Exception:
        return {
            "ip": ip_address,
            "country": "Unknown",
            "iso_code": "N/A",
            "provider": "GeoLite2"
        }

@router.get("/settings/modules/maxmind/download")
def download_maxmind_geoip(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.require_admin)
):
    user_id_entry = db.query(Module).filter(Module.name == "MaxMind-GeoIP-UserID", Module.is_local == True).first()
    license_key_entry = db.query(Module).filter(Module.name == "MaxMind-GeoIP-Key", Module.is_local == True).first()

    if not user_id_entry or not license_key_entry:
        params = urlencode({"error": "MaxMind credentials not found in module config."})
        return RedirectResponse(f"/web/v1/settings/modules/maxmind?{params}")

    account_id = user_id_entry.local_key.strip()
    license_key = license_key_entry.local_key.strip()

    url = "https://download.maxmind.com/geoip/databases/GeoLite2-Country/download?suffix=tar.gz"

    os.makedirs(RESOURCE_DIR, exist_ok=True)

    try:
        with requests.get(url, auth=(account_id, license_key), stream=True) as r:
            if r.status_code != 200:
                params = urlencode({"error": r.text})
                return RedirectResponse(f"/web/v1/settings/modules/maxmind?{params}")
            with open(GEOIP_TAR_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Extract .mmdb
        with tarfile.open(GEOIP_TAR_PATH, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith(".mmdb"):
                    tar.extract(member, RESOURCE_DIR)
                    extracted_path = os.path.join(RESOURCE_DIR, member.name)

                    # Safely remove old DB if it exists
                    if os.path.exists(GEOIP_DB_PATH):
                        os.remove(GEOIP_DB_PATH)

                    os.rename(extracted_path, GEOIP_DB_PATH)
                    break

        os.remove(GEOIP_TAR_PATH)

        global reader
        reader = geoip2.database.Reader(GEOIP_DB_PATH)

        params = urlencode({"success": "GeoIP database downloaded successfully!"})
        return RedirectResponse(f"/web/v1/settings/modules/maxmind?{params}")

    except Exception as e:
        params = urlencode({"error": f"Download failed: {str(e)}"})
        return RedirectResponse(f"/web/v1/settings/modules/maxmind?{params}")

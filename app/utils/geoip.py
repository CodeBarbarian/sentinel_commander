import os
import geoip2.database

# Path to GeoLite2 database
GEOIP_DB_PATH = os.path.join(os.path.dirname(__file__), "../resources/GeoLite2-Country.mmdb")

# Initialize reader only if the file exists
reader = None
if os.path.exists(GEOIP_DB_PATH):
    try:
        reader = geoip2.database.Reader(GEOIP_DB_PATH)
    except Exception:
        reader = None  # Fallback if reader fails to initialize

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

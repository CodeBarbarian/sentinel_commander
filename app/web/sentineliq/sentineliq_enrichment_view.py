from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Module
from app.utils import auth
from app.web.modules.maxmind_module import lookup_country
from app.web.modules.misp_module import MISPEnrichment
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/sentineliq/enrichment", response_class=HTMLResponse)
def sentinel_enrichment_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    return templates.TemplateResponse("sentineliq_enrichment/sentineliq_enrichment.html", {
        "request": request
    })

@router.get("/sentineliq/enrichment/api", response_class=HTMLResponse)
def enrichment_api(
    request: Request,
    value: str,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    results = []

    ## --- MAXMIND ---
    user_id_entry = db.query(Module).filter(Module.name == "MaxMind-GeoIP-UserID", Module.is_local == True).first()
    license_key_entry = db.query(Module).filter(Module.name == "MaxMind-GeoIP-Key", Module.is_local == True).first()
    maxmind_active = user_id_entry and license_key_entry

    if maxmind_active:
        from app.web.modules.maxmind_module import lookup_country
        geo_data = lookup_country(value)
        if geo_data and geo_data.get("country") != "Unknown":
            results.append({
                "title": "🌍 MaxMind Geolocation",
                "content": f"""
                    <strong>IP:</strong> {geo_data['ip']}<br>
                    <strong>Country:</strong> {geo_data['country']}<br>
                    <strong>ISO Code:</strong> {geo_data['iso_code']}<br>
                    <strong>Provider:</strong> {geo_data['provider']}
                """
            })

    ## --- MISP ---
    misp_entry = db.query(Module).filter(Module.name == "MISP", Module.is_local == False).first()
    misp_active = misp_entry and misp_entry.remote_url and misp_entry.remote_api_key

    if misp_active:
        from app.web.modules.misp_module import MISPEnrichment
        misp = MISPEnrichment(db)
        misp_result = misp.enrich_with_misp(value)
        if misp_result.get("matches", 0) > 0:
            match_html = ""
            for match in misp_result["data"]:
                event = match.get("event", {})
                match_html += f"""
                    <div class='mb-3 border-bottom pb-2'>
                        <strong>Type:</strong> {match['type']}<br>
                        <strong>Category:</strong> {match['category']}<br>
                        <strong>Value:</strong> {match['value']}<br>
                        <strong>Event:</strong> {event.get('info')}<br>
                        <strong>Date:</strong> {event.get('date')}<br>
                        <strong>Tags:</strong> {', '.join(match.get('tags', []))}
                    </div>
                """
            results.append({
                "title": "🧠 MISP Matches",
                "content": match_html
            })

    ## --- VIRUSTOTAL ---
    vt_entry = db.query(Module).filter(Module.name == "VirusTotal", Module.is_local == False).first()
    vt_active = vt_entry and vt_entry.remote_url and vt_entry.remote_api_key

    if vt_active:
        from app.web.modules.virustotal_module import VirusTotalEnrichment
        vt = VirusTotalEnrichment(db)
        vt_result = vt.lookup(value)
        if vt_result and not vt_result.get("error"):
            stats = vt_result.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            stats_html = "<br>".join([f"<strong>{k.title()}:</strong> {v}" for k, v in stats.items()])
            results.append({
                "title": "🦠 VirusTotal Lookup",
                "content": stats_html or "No stats available."
            })

    return templates.TemplateResponse("sentineliq_enrichment/results_embed.html", {
        "request": request,
        "results": results,
        "query": value
    })

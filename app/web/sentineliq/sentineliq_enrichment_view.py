from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
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

    # MaxMind
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

    # MISP
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

    return templates.TemplateResponse("sentineliq_enrichment/results_embed.html", {
        "request": request,
        "results": results,
        "query": value
    })

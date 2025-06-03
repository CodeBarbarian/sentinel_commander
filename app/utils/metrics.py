from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.case import Case
from sqlalchemy import func

def get_current_metrics(db: Session):
    return {
        "type": "metrics",
        "critical_alerts_count": db.query(func.count(Alert.id)).filter(Alert.severity == "critical", Alert.status == "new").scalar(),
        "open_alerts_count": db.query(func.count(Alert.id)).filter(Alert.status == "new").scalar(),
        "open_cases_count": db.query(func.count(Case.id)).filter(Case.state == "new").scalar()
    }
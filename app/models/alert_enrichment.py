from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class AlertEnrichment(Base):
    __tablename__ = "alert_enrichments"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), index=True, nullable=False)

    enrichment_type = Column(String(100), index=True)  # e.g., 'GeoIP', 'MISP', 'VirusTotal'
    source = Column(String(100), nullable=True)        # e.g., 'MISP Feed 1'
    data = Column(JSON, nullable=False)                # Flexible JSON payload
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    alert = relationship("Alert", back_populates="enrichments")

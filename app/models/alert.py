from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.orm import relationship

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)

    source = Column(String, index=True)
    source_ref_id = Column(String, index=True, nullable=True)
    severity = Column(Integer)
    message = Column(String)
    observables = Column(String, nullable=True)

    status = Column(String, default="new")  # new, in_progress, done, etc.
    resolution = Column(String, nullable=True)  # false_positive, true_positive, etc.
    resolution_comment = Column(String, nullable=True)

    tags = Column(String, default="")
    source_event_time = Column(DateTime, nullable=True)
    source_payload = Column(JSONB, nullable=True)

    agent_id = Column(String, index=True, nullable=True)
    agent_name = Column(String, index=True, nullable=True)
    agent_ip = Column(String, index=True, nullable=True)
    rule_id = Column(String, index=True, nullable=True)
    rule_description = Column(String, nullable=True)
    payload_flat_text = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    enrichments = relationship("AlertEnrichment", back_populates="alert", cascade="all, delete-orphan")

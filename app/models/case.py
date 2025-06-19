from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import engine, Base, get_db
from app.models.assets import Asset, case_asset_link

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Link to customer
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer = relationship("Customer", back_populates="cases")

    # Classification, State, Severity
    classification = Column(String, nullable=True)
    state = Column(String, default="new")
    severity = Column(Integer, default=5)  # Scale 0-15

    # Assignment
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_user = relationship("User")

    # Closing
    closing_note = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    # Tags
    tags = relationship("CaseTag", back_populates="case", cascade="all, delete-orphan")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    alerts = relationship("Alert", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")
    timeline = relationship("CaseTimelineEvent", back_populates="case", cascade="all, delete-orphan")
    tasks = relationship("CaseTask", back_populates="case", cascade="all, delete-orphan")
    evidence = relationship("CaseEvidence", back_populates="case", cascade="all, delete-orphan")
    iocs = relationship("CaseIOC", back_populates="case", cascade="all, delete-orphan")
    assets = relationship("Asset", secondary=case_asset_link, back_populates="linked_cases")
    playbooks = relationship("CasePlaybook", back_populates="case", cascade="all, delete-orphan")

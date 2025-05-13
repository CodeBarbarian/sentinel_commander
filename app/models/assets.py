from sqlalchemy import Column, Integer, String, Text, DateTime, func, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table for many-to-many Case <-> Asset relationship
case_asset_link = Table(
    "case_asset_link",
    Base.metadata,
    Column("case_id", Integer, ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column("asset_id", Integer, ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
)

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    hostname = Column(String, nullable=True)
    type = Column(String, nullable=True)  # E.g., server, endpoint, router, etc.
    owner = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Linked cases (many-to-many)
    linked_cases = relationship("Case", secondary="case_asset_link", back_populates="assets")

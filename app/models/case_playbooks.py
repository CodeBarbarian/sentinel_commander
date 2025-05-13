from sqlalchemy import Column, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

# Association table (many-to-many)
class CasePlaybook(Base):
    __tablename__ = "case_playbooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    playbook_id = Column(Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="playbooks")
    playbook = relationship("Playbook", back_populates="cases")
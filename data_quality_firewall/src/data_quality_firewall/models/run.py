from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from sqlalchemy import Column, String, DateTime, Integer


from data_quality_firewall.db.database import Base


class FileRun(Base):
    __tablename__ = "file_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="RECEIVED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    total_rows = Column(Integer, nullable=True)
    valid_rows = Column(Integer, nullable=True)
    invalid_rows = Column(Integer, nullable=True)

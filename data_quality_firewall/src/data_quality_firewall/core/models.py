from enum import Enum
from datetime import datetime, UTC
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FileRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    status: RunStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)

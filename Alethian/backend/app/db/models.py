from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Enum, JSON
import uuid
import datetime
import enum

Base = declarative_base()

class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    failed = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    status = Column(Enum(DocumentStatus), default=DocumentStatus.pending)
    meta_data = Column(JSON, nullable=True)

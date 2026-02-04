"""
Database models for Norwegian Aquaculture Regulatory Monitor
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime,
    Boolean, Float, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum

Base = declarative_base()


class ChangeType(enum.Enum):
    """Types of detected changes"""
    NEW_CONTENT = "new_content"
    MODIFIED = "modified"
    REMOVED = "removed"
    STRUCTURAL = "structural"


class Priority(enum.Enum):
    """Priority levels for changes"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DeliveryStatus(enum.Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Source(Base):
    """Monitored website sources"""
    __tablename__ = "sources"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)
    check_interval_hours = Column(Integer, default=4)
    priority = Column(String(20), default="medium")
    selectors = Column(JSON)  # CSS selectors for content extraction
    is_active = Column(Boolean, default=True)
    last_checked = Column(DateTime)
    last_changed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    snapshots = relationship("Snapshot", back_populates="source")
    changes = relationship("Change", back_populates="source")


class Snapshot(Base):
    """Content snapshots for change detection"""
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), ForeignKey("sources.id"), nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA-256
    content_text = Column(Text)  # Extracted text content
    content_html = Column(Text)  # Raw HTML (compressed)
    word_count = Column(Integer)
    captured_at = Column(DateTime, default=datetime.utcnow)
    http_status = Column(Integer)
    response_time_ms = Column(Integer)

    # Relationships
    source = relationship("Source", back_populates="snapshots")


class Change(Base):
    """Detected changes between snapshots"""
    __tablename__ = "changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(50), ForeignKey("sources.id"), nullable=False)
    previous_snapshot_id = Column(Integer, ForeignKey("snapshots.id"))
    current_snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False)

    change_type = Column(String(20), nullable=False)
    change_percent = Column(Float)  # Percentage of content changed
    diff_text = Column(Text)  # Human-readable diff
    added_text = Column(Text)  # New content added
    removed_text = Column(Text)  # Content removed

    # AI Analysis
    summary_no = Column(Text)  # Norwegian summary
    summary_en = Column(Text)  # English summary (optional)
    impact_analysis = Column(Text)
    affected_parties = Column(JSON)  # List of affected stakeholders
    action_items = Column(JSON)  # List of required actions
    deadlines = Column(JSON)  # Extracted deadlines
    keywords_found = Column(JSON)  # Significant keywords detected

    priority = Column(String(20), default="medium")
    is_significant = Column(Boolean, default=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships
    source = relationship("Source", back_populates="changes")
    notifications = relationship("Notification", back_populates="change")


class Client(Base):
    """Client/subscriber information"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    organization = Column(String(200))
    email = Column(String(200), nullable=False, unique=True)
    tier = Column(String(20), default="basic")  # basic, pro, enterprise
    is_active = Column(Boolean, default=True)

    # Notification preferences
    email_enabled = Column(Boolean, default=True)
    slack_enabled = Column(Boolean, default=False)
    slack_webhook_url = Column(String(500))
    slack_channel = Column(String(100))

    # Filter preferences
    categories = Column(JSON)  # List of categories to monitor
    priority_threshold = Column(String(20), default="low")  # Minimum priority
    keywords = Column(JSON)  # Custom keywords to watch

    # Digest preferences
    digest_frequency = Column(String(20), default="daily")  # realtime, hourly, daily, weekly
    digest_time = Column(String(5), default="07:00")  # HH:MM in Oslo time

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notifications = relationship("Notification", back_populates="client")


class Notification(Base):
    """Sent notifications tracking"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    change_id = Column(Integer, ForeignKey("changes.id"), nullable=False)

    delivery_method = Column(String(20), nullable=False)  # email, slack
    status = Column(String(20), default="pending")

    # Email specifics
    email_subject = Column(String(500))
    email_body = Column(Text)

    # Slack specifics
    slack_message = Column(Text)
    slack_thread_ts = Column(String(50))

    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="notifications")
    change = relationship("Change", back_populates="notifications")


class DigestQueue(Base):
    """Queue for digest emails"""
    __tablename__ = "digest_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    change_id = Column(Integer, ForeignKey("changes.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    included_in_digest = Column(Boolean, default=False)
    digest_sent_at = Column(DateTime)


def init_database(database_url: str = "sqlite:///data/aquaregwatch.db"):
    """Initialize the database and create all tables"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def get_session(database_url: str = "sqlite:///data/aquaregwatch.db"):
    """Get a database session"""
    engine = create_engine(database_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()

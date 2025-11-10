"""Database Models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class CategoryEnum(enum.Enum):
    """News category enumeration"""
    ROBOTICS = "ROBOTICS"
    AI = "AI"
    DEVELOPMENT = "DEVELOPMENT"


class News(Base):
    """News Article Model"""
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    site = Column(String(200), nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)

    # Content
    content = Column(Text, nullable=True)  # Full article content
    summary = Column(Text, nullable=True)  # AI-generated summary

    # Media
    image_url = Column(String(1000), nullable=True)  # Representative image
    video_url = Column(String(1000), nullable=True)  # Generated video (Sora)

    # Metadata
    published_at = Column(DateTime, nullable=True)  # Article publish date
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Processing flags
    crawled = Column(Boolean, default=False)  # Successfully crawled
    summarized = Column(Boolean, default=False)  # Summary generated
    video_generated = Column(Boolean, default=False)  # Video created
    sent = Column(Boolean, default=False)  # Email sent

    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title[:50]}...', site='{self.site}')>"


class ProcessingLog(Base):
    """Processing Log Model - Track daily processing runs"""
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Statistics
    articles_crawled = Column(Integer, default=0)
    articles_summarized = Column(Integer, default=0)
    videos_generated = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)

    # Status
    status = Column(String(50), default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ProcessingLog(id={self.id}, run_date='{self.run_date}', status='{self.status}')>"

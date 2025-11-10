"""Database Connection and Session Management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from .models import Base
from loguru import logger


class Database:
    """Database Manager"""

    def __init__(self, config):
        """
        Initialize database connection

        Args:
            config (dict): Database configuration from config.yaml
        """
        self.config = config
        self.engine = None
        self.session_factory = None
        self.Session = None

    def init_db(self):
        """Initialize database connection and create tables"""
        db_type = self.config.get("type", "sqlite")

        if db_type == "sqlite":
            db_path = self.config["sqlite"]["path"]
            # Create data directory if not exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db_url = f"sqlite:///{db_path}"

            # For SQLite, use StaticPool to avoid threading issues
            self.engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        elif db_type == "postgresql":
            pg_config = self.config["postgresql"]
            db_url = (
                f"postgresql://{pg_config['user']}:{pg_config['password']}"
                f"@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
            )
            self.engine = create_engine(db_url, echo=False)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Create session factory
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

        # Create all tables
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized: {db_type}")

    def get_session(self):
        """Get a new database session"""
        if self.Session is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return self.Session()

    def close(self):
        """Close database connection"""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connection closed")


# Global database instance
_db_instance = None


def get_db():
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        raise RuntimeError("Database not initialized")
    return _db_instance


def init_database(config):
    """Initialize global database instance"""
    global _db_instance
    _db_instance = Database(config)
    _db_instance.init_db()
    return _db_instance

"""
Reset sent flag for all news articles
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.utils import load_config
from src.database.db import init_database
from src.database.models import News


def main():
    """Reset sent flag to False for all articles"""
    print("=" * 60)
    print("Resetting sent flag for all articles")
    print("=" * 60)
    print()

    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

    # Initialize database
    try:
        db = init_database(config["database"])
        session = db.get_session()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return 1

    try:
        # Count articles with sent=True
        sent_count = session.query(News).filter_by(sent=True).count()
        total_count = session.query(News).count()

        print(f"Total articles: {total_count}")
        print(f"Articles with sent=True: {sent_count}")
        print()

        if sent_count == 0:
            print("No articles to reset. All sent flags are already False.")
            return 0

        # Reset all sent flags to False
        updated = session.query(News).filter_by(sent=True).update({"sent": False})
        session.commit()

        print(f"Successfully reset {updated} articles")
        print(f"All sent flags are now set to False (0)")

        # Verify
        remaining = session.query(News).filter_by(sent=True).count()
        print(f"\nVerification: Articles with sent=True: {remaining}")

        return 0

    except Exception as e:
        session.rollback()
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    finally:
        if session:
            session.close()
        if db:
            db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

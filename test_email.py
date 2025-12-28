"""
Test Email Sending Only
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.utils import load_config, setup_logging
from src.database.db import init_database
from src.mailer.mailer import NewsMailer


def main():
    """Test email sending"""
    print("=" * 60)
    print("Testing Email Sending")
    print("=" * 60)
    print()

    # Load configuration
    try:
        config = load_config()
        setup_logging(config)
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
        # Send email digest
        logger.info("Sending email digest...")
        mailer = NewsMailer(config["email"], session)
        email_sent = mailer.send_daily_digest()

        if email_sent:
            logger.info("✅ Email sent successfully!")
            return 0
        else:
            logger.error("❌ Failed to send email")
            return 1

    except Exception as e:
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

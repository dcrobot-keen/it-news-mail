"""Test script for markdown export functionality"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.utils import load_config, setup_logging
from src.database.db import init_database
from src.exporter.markdown_exporter import MarkdownExporter


def test_markdown_export():
    """Test markdown export functionality"""
    print("=" * 60)
    print("Testing Markdown Export")
    print("=" * 60)
    print()

    try:
        # Load configuration
        config = load_config()
        setup_logging(config)
        logger.info("Configuration loaded")

        # Initialize database
        db = init_database(config["database"])
        session = db.get_session()
        logger.info("Database initialized")

        # Create exporter
        exporter = MarkdownExporter(config["exporter"], session)
        logger.info("Markdown exporter initialized")

        # Export all articles
        stats = exporter.export_all()

        print()
        print("=" * 60)
        print("Export Results:")
        print(f"  - Total articles: {stats['total']}")
        print(f"  - Files created: {stats['files_created']}")
        print(f"  - Output directory: {exporter.output_dir}")
        print("=" * 60)

        # Cleanup
        session.close()
        db.close()

        return 0

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = test_markdown_export()
    sys.exit(exit_code)

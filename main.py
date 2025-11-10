"""
IT News Mail - Main Entry Point

Daily IT news crawling, summarization, and email automation
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.utils import load_config, load_site_list, setup_logging
from src.database.db import init_database
from src.database.models import ProcessingLog
from src.crawler.crawler import NewsCrawler
from src.summarizer.summarizer import NewsSummarizer
from src.mailer.mailer import NewsMailer
from src.exporter.markdown_exporter import MarkdownExporter
from datetime import datetime


def main():
    """Main execution function"""
    print("=" * 60)
    print("IT News Mail Automation System")
    print("=" * 60)
    print()

    # Load configuration
    try:
        config = load_config()
        setup_logging(config)
        logger.info("Starting IT News Mail automation")

    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

    # Initialize database
    try:
        db = init_database(config["database"])
        session = db.get_session()

        # Create processing log
        log_entry = ProcessingLog(status="running")
        session.add(log_entry)
        session.commit()

    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return 1

    try:
        # Step 1: Load site list
        logger.info("Step 1: Loading site list")
        sites = load_site_list()
        logger.info(f"Loaded {len(sites)} sites")

        # Step 2: Crawl news
        logger.info("Step 2: Crawling news articles")
        crawler = NewsCrawler(config["crawler"], session)
        crawl_stats = crawler.crawl_all_sites(sites)
        log_entry.articles_crawled = crawl_stats["total_articles"]
        session.commit()

        logger.info(f"Crawled {crawl_stats['total_articles']} articles from {crawl_stats['successful_sites']} sites")

        # Step 3: Summarize articles
        logger.info("Step 3: Summarizing articles with AI")
        summarizer = NewsSummarizer(config["ai"], session)
        summary_stats = summarizer.summarize_all_unsummarized()
        log_entry.articles_summarized = summary_stats["successful"]
        session.commit()

        logger.info(f"Summarized {summary_stats['successful']}/{summary_stats['total']} articles")

        # Step 4: Send email digest
        logger.info("Step 4: Sending email digest")
        mailer = NewsMailer(config["email"], session)
        email_sent = mailer.send_daily_digest()

        if email_sent:
            log_entry.emails_sent = len(config["email"]["recipients"])
            logger.info("Email digest sent successfully")
        else:
            logger.warning("Failed to send email digest")

        # Step 5: Export to markdown files
        logger.info("Step 5: Exporting to markdown files")
        exporter = MarkdownExporter(config["exporter"], session)
        export_stats = exporter.export_all()
        logger.info(f"Exported {export_stats['total']} articles to {export_stats['files_created']} markdown files")

        # Update processing log
        log_entry.status = "completed"
        log_entry.completed_at = datetime.utcnow()
        session.commit()

        logger.info("=" * 60)
        logger.info("Processing completed successfully!")
        logger.info(f"  - Articles crawled: {log_entry.articles_crawled}")
        logger.info(f"  - Articles summarized: {log_entry.articles_summarized}")
        logger.info(f"  - Emails sent: {log_entry.emails_sent}")
        logger.info(f"  - Markdown files created: {export_stats['files_created']}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Error during processing: {e}", exc_info=True)

        # Update processing log
        log_entry.status = "failed"
        log_entry.error_message = str(e)
        log_entry.completed_at = datetime.utcnow()
        session.commit()

        return 1

    finally:
        # Cleanup
        if session:
            session.close()
        if db:
            db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

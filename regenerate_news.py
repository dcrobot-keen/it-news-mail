"""
Regenerate news summaries and markdown for a specific date
"""
from datetime import datetime
from pathlib import Path
import sys

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils import load_config
from src.database.db import init_database
from src.database.models import News
from src.summarizer.summarizer import NewsSummarizer
from src.exporter.markdown_exporter import MarkdownExporter


def reset_news_by_date(session, target_date_str):
    """Reset sent and summarized flags for articles on a specific date"""
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        print(f"Invalid date format: {target_date_str}. Use YYYY-MM-DD")
        return 0

    # Get articles for the target date
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    articles = session.query(News).filter(
        News.created_at >= start_of_day,
        News.created_at <= end_of_day
    ).all()

    if not articles:
        print(f"No articles found for {target_date_str}")
        return 0

    print(f"Found {len(articles)} articles for {target_date_str}")

    # Reset flags and clear summary
    for article in articles:
        article.summarized = False
        article.sent = False
        article.summary = None
        try:
            print(f"  Reset: {article.title[:60]}...")
        except UnicodeEncodeError:
            print(f"  Reset: [Article title with special characters]")

    session.commit()
    print(f"Reset {len(articles)} articles")
    return len(articles)


def main():
    """Main execution function"""
    target_date = "2025-12-27"

    print("=" * 60)
    print(f"Regenerating news for {target_date}")
    print("=" * 60)
    print()

    # Load configuration
    config = load_config()

    # Initialize database
    db = init_database(config["database"])
    session = db.get_session()

    try:
        # Step 1: Reset articles
        print("Step 1: Resetting articles...")
        count = reset_news_by_date(session, target_date)
        if count == 0:
            return

        print()

        # Step 2: Regenerate summaries
        print("Step 2: Regenerating summaries with updated prompt...")
        summarizer = NewsSummarizer(config["ai"], session)
        summary_stats = summarizer.summarize_all_unsummarized()
        print(f"Summarized {summary_stats['successful']}/{summary_stats['total']} articles")
        print()

        # Step 3: Regenerate markdown
        print("Step 3: Regenerating markdown file...")
        exporter = MarkdownExporter(config["exporter"], session)
        file_path = exporter.export_by_date(target_date)

        if file_path:
            print(f"Created markdown file: {file_path}")
        else:
            print("Failed to create markdown file")

        print()
        print("=" * 60)
        print("Regeneration completed!")
        print("=" * 60)

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        return 1

    finally:
        session.close()
        db.close()

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

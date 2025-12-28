"""Markdown Exporter Module - Export news to markdown files by date"""
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from loguru import logger
from ..database.models import News, CategoryEnum


class MarkdownExporter:
    """Export news articles to markdown files grouped by date"""

    def __init__(self, config, db_session):
        """
        Initialize Markdown Exporter

        Args:
            config (dict): Exporter configuration
            db_session: SQLAlchemy database session
        """
        self.config = config
        self.session = db_session
        self.output_dir = Path(config.get("output_dir", "output/markdown"))

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Markdown exporter initialized. Output directory: {self.output_dir}")

    def export_all(self):
        """
        Export all summarized articles to markdown files grouped by date

        Returns:
            dict: Export statistics
        """
        # Get all summarized articles
        articles = self.session.query(News).filter_by(
            summarized=True
        ).order_by(News.created_at.desc()).all()

        if not articles:
            logger.info("No articles to export")
            return {"total": 0, "files_created": 0}

        logger.info(f"Found {len(articles)} articles to export")

        # Group articles by date
        articles_by_date = self._group_by_date(articles)

        stats = {
            "total": len(articles),
            "files_created": 0,
        }

        # Create markdown file for each date
        for date_str, date_articles in articles_by_date.items():
            file_path = self.output_dir / f"news_{date_str}.md"
            self._create_markdown_file(file_path, date_str, date_articles)
            stats["files_created"] += 1
            logger.info(f"Created markdown file: {file_path}")

        logger.info(f"Export completed: {stats}")
        return stats

    def export_by_date(self, target_date):
        """
        Export articles for a specific date

        Args:
            target_date (datetime or str): Target date (YYYY-MM-DD format if string)

        Returns:
            str: Path to created file or None
        """
        # Convert string to datetime if necessary
        if isinstance(target_date, str):
            try:
                target_date = datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Invalid date format: {target_date}. Use YYYY-MM-DD")
                return None

        # Get articles for the target date
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        articles = self.session.query(News).filter(
            News.summarized == True,
            News.created_at >= start_of_day,
            News.created_at <= end_of_day
        ).order_by(News.category, News.created_at.desc()).all()

        if not articles:
            logger.info(f"No articles found for {target_date.strftime('%Y-%m-%d')}")
            return None

        # Create markdown file
        date_str = target_date.strftime("%Y-%m-%d")
        file_path = self.output_dir / f"news_{date_str}.md"
        self._create_markdown_file(file_path, date_str, articles)

        logger.info(f"Created markdown file: {file_path}")
        return str(file_path)

    def _group_by_date(self, articles):
        """
        Group articles by date

        Args:
            articles (list): List of News objects

        Returns:
            dict: Articles grouped by date (YYYY-MM-DD)
        """
        grouped = defaultdict(list)

        for article in articles:
            # Use created_at or published_at for grouping
            date_obj = article.published_at if article.published_at else article.created_at
            date_str = date_obj.strftime("%Y-%m-%d")
            grouped[date_str].append(article)

        return dict(grouped)

    def _create_markdown_file(self, file_path, date_str, articles):
        """
        Create markdown file for a specific date

        Args:
            file_path (Path): Output file path
            date_str (str): Date string (YYYY-MM-DD)
            articles (list): List of News objects
        """
        # Category metadata
        category_info = {
            CategoryEnum.ROBOTICS: {"emoji": "🤖", "name": "로보틱스"},
            CategoryEnum.AI: {"emoji": "🧠", "name": "인공지능"},
            CategoryEnum.DEVELOPMENT: {"emoji": "💻", "name": "개발 뉴스"},
        }

        # Group articles by category
        articles_by_category = defaultdict(list)
        for article in articles:
            articles_by_category[article.category].append(article)

        # Build markdown content
        md_lines = [
            f"# 📰 IT News Digest - {date_str}",
            "",
            f"**생성일시:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**총 {len(articles)}개 기사**",
            "",
            "---",
            "",
        ]

        # Add articles by category
        for category in [CategoryEnum.ROBOTICS, CategoryEnum.AI, CategoryEnum.DEVELOPMENT]:
            if category not in articles_by_category or not articles_by_category[category]:
                continue

            cat_info = category_info[category]
            cat_articles = articles_by_category[category]

            md_lines.extend([
                f"## {cat_info['emoji']} {cat_info['name']}",
                "",
            ])

            for article in cat_articles:
                md_lines.extend(self._format_article(article))
                md_lines.append("")

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    def _format_article(self, article):
        """
        Format a single article as markdown

        Args:
            article (News): News object

        Returns:
            list: List of markdown lines
        """
        # Extract Korean title if available in summary
        title_display = article.title
        if article.summary:
            title_match = re.match(r'^제목:\s*(.+)$', article.summary, re.MULTILINE)
            if title_match:
                korean_title = title_match.group(1).strip()
                title_display = f"{article.title} ({korean_title})"

        lines = [
            f"### {title_display}",
            "",
        ]

        # Add image if available
        if article.image_url:
            lines.extend([
                f"![{article.title}]({article.image_url})",
                "",
            ])

        # Add metadata
        pub_date = article.published_at.strftime('%Y-%m-%d %H:%M') if article.published_at else 'N/A'
        lines.extend([
            f"**출처:** {article.site} | **날짜:** {pub_date}",
            "",
        ])

        # Add summary (remove title line if present)
        if article.summary:
            summary_text = article.summary
            # Remove "제목: ..." line from summary
            summary_text = re.sub(r'^제목:\s*.+\n\n?', '', summary_text, flags=re.MULTILINE)
            lines.extend([
                summary_text.strip(),
                "",
            ])

        # Add link
        lines.extend([
            f"[원문 보기]({article.url})",
            "",
            "---",
            "",
        ])

        return lines

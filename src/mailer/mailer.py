"""Email Mailer Module"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from loguru import logger
from ..database.models import News, CategoryEnum


class NewsMailer:
    """Email Mailer for sending news summaries"""

    def __init__(self, config, db_session):
        """
        Initialize News Mailer

        Args:
            config (dict): Email configuration
            db_session: SQLAlchemy database session
        """
        self.config = config
        self.session = db_session
        self.smtp_config = config["smtp"]
        self.from_email = config["from"]
        self.recipients = config["recipients"]

    def send_daily_digest(self):
        """
        Send daily news digest to all recipients

        Returns:
            bool: True if successful, False otherwise
        """
        # Get all summarized but not sent articles
        news_items = self.session.query(News).filter_by(
            summarized=True,
            sent=False
        ).order_by(News.category, News.published_at.desc()).all()

        if not news_items:
            logger.info("No news to send")
            return True

        logger.info(f"Preparing to send {len(news_items)} articles")

        # Group by category
        news_by_category = self._group_by_category(news_items)

        # Generate HTML email
        html_content = self._generate_html_email(news_by_category)

        # Send email
        try:
            subject = f"IT News Digest - {datetime.now().strftime('%Y-%m-%d')}"
            self._send_email(subject, html_content)

            # Mark all articles as sent
            for news in news_items:
                news.sent = True
            self.session.commit()

            logger.info(f"Successfully sent email to {len(self.recipients)} recipients")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error sending email: {e}")
            return False

    def _group_by_category(self, news_items):
        """
        Group news items by category

        Args:
            news_items (list): List of News objects

        Returns:
            dict: News items grouped by category
        """
        grouped = {
            CategoryEnum.ROBOTICS: [],
            CategoryEnum.AI: [],
            CategoryEnum.DEVELOPMENT: [],
        }

        for news in news_items:
            grouped[news.category].append(news)

        return grouped

    def _generate_html_email(self, news_by_category):
        """
        Generate HTML email content

        Args:
            news_by_category (dict): News items grouped by category

        Returns:
            str: HTML content
        """
        category_names = {
            CategoryEnum.ROBOTICS: "🤖 로보틱스",
            CategoryEnum.AI: "🧠 인공지능",
            CategoryEnum.DEVELOPMENT: "💻 개발 뉴스",
        }

        html_parts = [
            """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    .header {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        border-radius: 10px;
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .category {
                        margin: 30px 0;
                    }
                    .category-title {
                        font-size: 24px;
                        font-weight: bold;
                        color: #667eea;
                        border-bottom: 3px solid #667eea;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }
                    .article {
                        background: #f8f9fa;
                        border-left: 4px solid #667eea;
                        padding: 20px;
                        margin-bottom: 20px;
                        border-radius: 5px;
                    }
                    .article-title {
                        font-size: 18px;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 10px;
                    }
                    .article-meta {
                        font-size: 12px;
                        color: #666;
                        margin-bottom: 10px;
                    }
                    .article-summary {
                        font-size: 14px;
                        line-height: 1.8;
                        color: #555;
                    }
                    .article-link {
                        display: inline-block;
                        margin-top: 10px;
                        color: #667eea;
                        text-decoration: none;
                        font-weight: bold;
                    }
                    .article-link:hover {
                        text-decoration: underline;
                    }
                    .footer {
                        text-align: center;
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #ddd;
                        color: #666;
                        font-size: 12px;
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📰 IT News Daily Digest</h1>
                    <p>""" + datetime.now().strftime('%Y년 %m월 %d일') + """</p>
                </div>
            """
        ]

        # Add news by category
        for category, news_items in news_by_category.items():
            if not news_items:
                continue

            html_parts.append(f'<div class="category">')
            html_parts.append(f'<div class="category-title">{category_names[category]}</div>')

            for news in news_items:
                html_parts.append(f'''
                <div class="article">
                    <div class="article-title">{news.title}</div>
                    <div class="article-meta">
                        {news.site} | {news.published_at.strftime('%Y-%m-%d %H:%M') if news.published_at else 'N/A'}
                    </div>
                    <div class="article-summary">
                        {news.summary if news.summary else '요약이 생성되지 않았습니다.'}
                    </div>
                    <a href="{news.url}" class="article-link" target="_blank">원문 보기 →</a>
                </div>
                ''')

            html_parts.append('</div>')

        # Add footer
        html_parts.append("""
                <div class="footer">
                    <p>이 이메일은 자동으로 생성되었습니다.</p>
                    <p>IT News Mail Automation System</p>
                </div>
            </body>
            </html>
        """)

        return ''.join(html_parts)

    def _html_to_plain_text(self, html_content):
        """
        Convert HTML email to plain text for clients that don't support HTML

        Args:
            html_content (str): HTML content

        Returns:
            str: Plain text version
        """
        import re
        from html import unescape

        # Remove HTML tags
        text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        text = unescape(text)

        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()

        return text

    def _send_email(self, subject, html_content):
        """
        Send email via SMTP

        Args:
            subject (str): Email subject
            html_content (str): HTML email content
        """
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.recipients)

        # Generate plain text version for email clients that don't support HTML
        plain_text = self._html_to_plain_text(html_content)
        text_part = MIMEText(plain_text, 'plain', 'utf-8')
        msg.attach(text_part)

        # Attach HTML content (should be attached AFTER plain text for proper fallback)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
            if self.smtp_config.get('use_tls', True):
                server.starttls()

            server.login(self.smtp_config['user'], self.smtp_config['password'])
            server.send_message(msg)

        logger.info(f"Email sent: {subject}")

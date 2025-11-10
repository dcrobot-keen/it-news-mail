"""News Summarizer Module using AI APIs"""
import requests
from bs4 import BeautifulSoup
from loguru import logger
from ..database.models import News


class NewsSummarizer:
    """News Summarizer using OpenAI or Anthropic APIs"""

    def __init__(self, config, db_session):
        """
        Initialize News Summarizer

        Args:
            config (dict): AI configuration
            db_session: SQLAlchemy database session
        """
        self.config = config
        self.session = db_session
        self.provider = config.get("provider", "openai")
        self.max_summary_length = config.get("max_summary_length", 500)

        if self.provider == "openai":
            self.api_config = config["openai"]
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_config["api_key"])
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
                self.client = None
        elif self.provider == "anthropic":
            self.api_config = config["anthropic"]
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_config["api_key"])
            except ImportError:
                logger.error("Anthropic package not installed. Run: pip install anthropic")
                self.client = None
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    def summarize_article(self, news_id):
        """
        Summarize a single article

        Args:
            news_id (int): News article ID

        Returns:
            bool: True if successful, False otherwise
        """
        # Get news article from database
        news = self.session.query(News).filter_by(id=news_id).first()
        if not news:
            logger.error(f"News article not found: {news_id}")
            return False

        if news.summarized:
            logger.info(f"Article already summarized: {news.title[:50]}...")
            return True

        try:
            # Fetch full article content if not already fetched
            if not news.content:
                content = self._fetch_article_content(news.url)
                if not content:
                    logger.warning(f"Could not fetch content for: {news.url}")
                    return False
                news.content = content
                self.session.commit()

            # Generate summary using AI
            summary = self._generate_summary(news.title, news.content, news.category.value)
            if not summary:
                logger.error(f"Failed to generate summary for: {news.title[:50]}...")
                return False

            # Update news with summary
            news.summary = summary
            news.summarized = True
            self.session.commit()

            logger.info(f"Summarized: {news.title[:50]}...")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error summarizing article {news_id}: {e}")
            return False

    def _fetch_article_content(self, url):
        """
        Fetch full article content from URL

        Args:
            url (str): Article URL

        Returns:
            str: Article content or None
        """
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Try to find main content
            # Common content containers
            content_selectors = [
                "article",
                ".article-content",
                ".post-content",
                ".entry-content",
                "main",
                ".content",
            ]

            content = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator="\n", strip=True)
                    break

            # Fallback to body if no content found
            if not content:
                body = soup.find("body")
                if body:
                    content = body.get_text(separator="\n", strip=True)

            # Limit content length
            if content and len(content) > 10000:
                content = content[:10000]

            return content

        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return None

    def _generate_summary(self, title, content, category):
        """
        Generate summary using AI API

        Args:
            title (str): Article title
            content (str): Article content
            category (str): Article category

        Returns:
            str: Summary or None
        """
        if not self.client:
            logger.error("AI client not initialized")
            return None

        try:
            # Create prompt
            prompt = self._create_summary_prompt(title, content, category)

            # Generate summary based on provider
            if self.provider == "openai":
                summary = self._generate_openai_summary(prompt)
            elif self.provider == "anthropic":
                summary = self._generate_anthropic_summary(prompt)
            else:
                return None

            return summary

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    def _create_summary_prompt(self, title, content, category):
        """
        Create prompt for AI summary generation

        Args:
            title (str): Article title
            content (str): Article content
            category (str): Article category

        Returns:
            str: Prompt
        """
        prompt = f"""다음 {category} 분야의 뉴스 기사를 한국어로 요약해주세요.

제목: {title}

내용:
{content}

요구사항:
1. 핵심 내용을 {self.max_summary_length}자 이내로 간결하게 요약
2. 기술적 용어는 설명을 추가
3. 주요 수치나 날짜가 있다면 포함
4. 왜 중요한지, 어떤 영향이 있을지 설명
5. 한국어로 작성

요약:"""

        return prompt

    def _generate_openai_summary(self, prompt):
        """Generate summary using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.api_config["model"],
                messages=[
                    {"role": "system", "content": "당신은 IT 뉴스를 전문적으로 요약하는 AI 어시스턴트입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.api_config.get("max_tokens", 1000),
                temperature=0.7,
            )

            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def _generate_anthropic_summary(self, prompt):
        """Generate summary using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.api_config["model"],
                max_tokens=self.api_config.get("max_tokens", 1000),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary = response.content[0].text.strip()
            return summary

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None

    def summarize_all_unsummarized(self):
        """
        Summarize all articles that haven't been summarized yet

        Returns:
            dict: Summary statistics
        """
        # Get all unsummarized articles
        unsummarized = self.session.query(News).filter_by(
            crawled=True,
            summarized=False
        ).all()

        stats = {
            "total": len(unsummarized),
            "successful": 0,
            "failed": 0,
        }

        logger.info(f"Found {stats['total']} articles to summarize")

        for news in unsummarized:
            if self.summarize_article(news.id):
                stats["successful"] += 1
            else:
                stats["failed"] += 1

        logger.info(f"Summarization completed: {stats}")
        return stats

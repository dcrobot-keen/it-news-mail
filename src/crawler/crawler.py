"""News Crawler Module"""
import time
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
from loguru import logger
from ..database.models import News, CategoryEnum


class NewsCrawler:
    """News Crawler for fetching articles from various sites"""

    def __init__(self, config, db_session):
        """
        Initialize News Crawler

        Args:
            config (dict): Crawler configuration
            db_session: SQLAlchemy database session
        """
        self.config = config
        self.session = db_session
        self.user_agent = config.get("user_agent", "Mozilla/5.0")
        self.timeout = config.get("timeout", 30)
        self.max_retries = config.get("max_retries", 3)
        self.delay = config.get("delay_between_requests", 2)

    def crawl_site(self, site_info):
        """
        Crawl a single site for news articles

        Args:
            site_info (dict): Site information from site-list.txt

        Returns:
            list: List of crawled articles
        """
        logger.info(f"Crawling {site_info['site_name']} ({site_info['url']})")

        try:
            # Fetch page content
            html_content = self._fetch_page(site_info["url"])
            if not html_content:
                return []

            # Parse articles
            articles = self._parse_articles(html_content, site_info)

            # Save to database
            saved_count = 0
            for article in articles:
                if self._save_article(article, site_info):
                    saved_count += 1

            logger.info(f"Saved {saved_count}/{len(articles)} articles from {site_info['site_name']}")

            # Delay between requests
            time.sleep(self.delay)

            return articles

        except Exception as e:
            logger.error(f"Error crawling {site_info['site_name']}: {e}")
            return []

    def _fetch_page(self, url):
        """
        Fetch page content with retry logic

        Args:
            url (str): URL to fetch

        Returns:
            str: HTML content or None
        """
        headers = {"User-Agent": self.user_agent}

        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.text

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None

    def _parse_articles(self, html_content, site_info):
        """
        Parse articles from HTML content

        Args:
            html_content (str): HTML content
            site_info (dict): Site information

        Returns:
            list: List of article dictionaries
        """
        soup = BeautifulSoup(html_content, "lxml")
        articles = []

        try:
            # Select articles based on selector type
            if site_info["selector_type"] == "css":
                article_elements = soup.select(site_info["article_selector"])
            else:  # xpath (not directly supported by BeautifulSoup)
                logger.warning(f"XPath selector not fully supported, using CSS instead")
                article_elements = soup.select(site_info["article_selector"])

            for element in article_elements[:10]:  # Limit to 10 articles per site
                article = self._extract_article_info(element, site_info)
                if article:
                    articles.append(article)

        except Exception as e:
            logger.error(f"Error parsing articles from {site_info['site_name']}: {e}")

        return articles

    def _extract_article_info(self, element, site_info):
        """
        Extract article information from HTML element

        Args:
            element: BeautifulSoup element
            site_info (dict): Site information

        Returns:
            dict: Article information or None
        """
        try:
            # Try to find title
            title_elem = element.find(["h1", "h2", "h3", "h4", "a"])
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                return None

            # Try to find URL
            link_elem = element.find("a")
            if link_elem and link_elem.get("href"):
                url = link_elem["href"]
                # Convert relative URL to absolute
                if url.startswith("/"):
                    from urllib.parse import urljoin
                    url = urljoin(site_info["url"], url)
            else:
                url = site_info["url"]  # Fallback to site URL

            # Try to find image
            img_elem = element.find("img")
            image_url = None
            if img_elem:
                image_url = img_elem.get("src") or img_elem.get("data-src")
                if image_url and image_url.startswith("/"):
                    from urllib.parse import urljoin
                    image_url = urljoin(site_info["url"], image_url)

            # Try to extract published date (this is site-specific, so just use current time)
            published_at = datetime.utcnow()

            return {
                "title": title,
                "url": url,
                "image_url": image_url,
                "published_at": published_at,
            }

        except Exception as e:
            logger.warning(f"Error extracting article info: {e}")
            return None

    def _save_article(self, article, site_info):
        """
        Save article to database if not already exists

        Args:
            article (dict): Article information
            site_info (dict): Site information

        Returns:
            bool: True if saved, False if already exists
        """
        try:
            # Check if article already exists
            existing = self.session.query(News).filter_by(url=article["url"]).first()
            if existing:
                logger.debug(f"Article already exists: {article['title'][:50]}...")
                return False

            # Create new news entry
            news = News(
                title=article["title"],
                url=article["url"],
                site=site_info["site_name"],
                category=CategoryEnum[site_info["category"]],
                image_url=article.get("image_url"),
                published_at=article.get("published_at"),
                crawled=True,
            )

            self.session.add(news)
            self.session.commit()

            logger.debug(f"Saved article: {article['title'][:50]}...")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving article: {e}")
            return False

    def crawl_all_sites(self, sites):
        """
        Crawl all sites from site list

        Args:
            sites (list): List of site information dictionaries

        Returns:
            dict: Crawling statistics
        """
        stats = {
            "total_sites": len(sites),
            "successful_sites": 0,
            "total_articles": 0,
        }

        for site_info in sites:
            articles = self.crawl_site(site_info)
            if articles:
                stats["successful_sites"] += 1
                stats["total_articles"] += len(articles)

        logger.info(f"Crawling completed: {stats}")
        return stats

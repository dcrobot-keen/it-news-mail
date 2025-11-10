"""Test cases for crawler module"""
import pytest
from src.crawler.crawler import NewsCrawler


def test_crawler_initialization():
    """Test crawler initialization"""
    config = {
        "user_agent": "Test Agent",
        "timeout": 30,
        "max_retries": 3,
        "delay_between_requests": 1,
    }

    crawler = NewsCrawler(config, None)

    assert crawler.user_agent == "Test Agent"
    assert crawler.timeout == 30
    assert crawler.max_retries == 3
    assert crawler.delay == 1


# Add more tests as needed

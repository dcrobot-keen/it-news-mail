"""Utility functions"""
import os
import yaml
import re
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


def load_config(config_path="config/config.yaml"):
    """
    Load configuration from YAML file with environment variable substitution

    Args:
        config_path (str): Path to config file

    Returns:
        dict: Configuration dictionary
    """
    # Load environment variables from .env file
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")

    # Load YAML config
    config_full_path = Path(__file__).parent.parent / config_path
    if not config_full_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_full_path}")

    with open(config_full_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Replace environment variables in config
    config = _substitute_env_vars(config)

    logger.info(f"Configuration loaded from {config_full_path}")
    return config


def _substitute_env_vars(obj):
    """
    Recursively substitute environment variables in config

    Replaces ${VAR_NAME} with environment variable value

    Args:
        obj: Configuration object (dict, list, or str)

    Returns:
        Object with substituted values
    """
    if isinstance(obj, dict):
        return {k: _substitute_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_substitute_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        # Replace ${VAR_NAME} with environment variable
        pattern = r"\$\{([^}]+)\}"
        matches = re.finditer(pattern, obj)
        result = obj
        for match in matches:
            var_name = match.group(1)
            var_value = os.getenv(var_name, "")
            result = result.replace(match.group(0), var_value)
        return result
    else:
        return obj


def load_site_list(site_list_path="site-list.txt"):
    """
    Load site list from text file

    Args:
        site_list_path (str): Path to site list file

    Returns:
        list: List of site dictionaries
    """
    site_list_full_path = Path(__file__).parent.parent / site_list_path
    if not site_list_full_path.exists():
        raise FileNotFoundError(f"Site list file not found: {site_list_full_path}")

    sites = []
    with open(site_list_full_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Parse line: category|site_name|url|selector_type|article_selector
            parts = line.split("|")
            if len(parts) != 5:
                logger.warning(f"Invalid site list entry: {line}")
                continue

            sites.append({
                "category": parts[0].strip(),
                "site_name": parts[1].strip(),
                "url": parts[2].strip(),
                "selector_type": parts[3].strip(),
                "article_selector": parts[4].strip(),
            })

    logger.info(f"Loaded {len(sites)} sites from {site_list_full_path}")
    return sites


def setup_logging(config):
    """
    Setup logging configuration

    Args:
        config (dict): Logging configuration
    """
    log_config = config.get("logging", {})
    log_level = log_config.get("level", "INFO")
    log_dir = log_config.get("log_dir", "logs")

    # Create log directory
    log_path = Path(__file__).parent.parent / log_dir
    log_path.mkdir(exist_ok=True)

    # Configure loguru
    logger.remove()  # Remove default handler

    # Console handler
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # File handler
    logger.add(
        log_path / "it-news-mail.log",
        rotation=log_config.get("max_file_size", "10 MB"),
        retention=log_config.get("backup_count", 5),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
    )

    logger.info("Logging configured")

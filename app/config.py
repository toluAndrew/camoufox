"""Configuration management for the web scraper service."""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from decouple import config


@dataclass(frozen=True)
class ScrapingConfig:
    """Configuration for web scraping operations."""

    default_wait_time: int = 5
    max_wait_time: int = 30
    default_headless: bool = True
    max_concurrent_requests: int = 10
    request_timeout: int = 60
    user_agent_rotation: bool = True
    default_remove_elements: List[str] = None

    def __post_init__(self) -> None:
        if self.default_remove_elements is None:
            object.__setattr__(self, 'default_remove_elements', [
                'script', 'style', 'noscript',
                'nav', 'header', 'footer',
                '.advertisement', '.ads', '.ad',
                '.social-share', '.social-sharing',
                '#comments', '.comments',
                '.sidebar', '.related-articles',
                '.newsletter-signup', '.popup',
                '.cookie-notice', '.gdpr-notice'
            ])


@dataclass(frozen=True)
class ContentProcessingConfig:
    """Configuration for content processing."""

    ignore_links: bool = True
    ignore_images: bool = True
    body_width: int = 0
    unicode_snob: bool = True
    ignore_emphasis: bool = False
    skip_internal_links: bool = True
    max_content_length: int = 1_000_000_000_000  # 1MB limit
    min_content_length: int = 100


@dataclass(frozen=True)
class AppConfig:
    """Main application configuration."""

    # Flask settings
    DEBUG: bool = config('DEBUG', default=False, cast=bool)
    TESTING: bool = config('TESTING', default=False, cast=bool)
    SECRET_KEY: str = config('SECRET_KEY', default='dev-secret-key')

    # API settings
    API_VERSION: str = config('API_VERSION', default='v1')
    MAX_CONTENT_LENGTH: int = config('MAX_CONTENT_LENGTH', default=16 * 1024 * 1024, cast=int)

    # Logging
    LOG_LEVEL: str = config('LOG_LEVEL', default='INFO')
    LOG_FORMAT: str = config('LOG_FORMAT', default='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # CORS
    CORS_ORIGINS: List[str] = field(
        default_factory=lambda: config('CORS_ORIGINS', default='*').split(',')
    )

    # Rate limiting
    RATELIMIT_ENABLED: bool = config('RATELIMIT_ENABLED', default=True, cast=bool)
    RATELIMIT_DEFAULT: str = config('RATELIMIT_DEFAULT', default='100 per hour')

    # Component configs
    scraping: ScrapingConfig = None
    content_processing: ContentProcessingConfig = None

    def __post_init__(self) -> None:
        if self.scraping is None:
            object.__setattr__(self, 'scraping', ScrapingConfig())
        if self.content_processing is None:
            object.__setattr__(self, 'content_processing', ContentProcessingConfig())


# Environment-specific configurations
class DevelopmentConfig(AppConfig):
    """Development configuration."""
    DEBUG: bool = True
    LOG_LEVEL: str = 'DEBUG'


class ProductionConfig(AppConfig):
    """Production configuration."""
    DEBUG: bool = False
    TESTING: bool = False
    LOG_LEVEL: str = 'WARNING'


class TestingConfig(AppConfig):
    """Testing configuration."""
    TESTING: bool = True
    DEBUG: bool = True
    LOG_LEVEL: str = 'DEBUG'


# Configuration factory
def get_config() -> AppConfig:
    """Get configuration based on environment."""
    env = config('FLASK_ENV', default='development').lower()

    config_map = {
        'development': DevelopmentConfig(),
        'production': ProductionConfig(),
        'testing': TestingConfig()
    }

    return config_map.get(env, DevelopmentConfig())
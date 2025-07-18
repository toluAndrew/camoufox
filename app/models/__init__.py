"""Data models for the web scraper service."""

from .scrape_request import ScrapeRequest, BatchScrapeRequest
from .scrape_response import ScrapeResponse, BatchScrapeResponse, ErrorResponse
from .exceptions import (
    ScrapingError,
    ValidationError,
    ContentProcessingError,
    NetworkError,
    TimeoutError
)

__all__ = [
    'ScrapeRequest',
    'BatchScrapeRequest',
    'ScrapeResponse',
    'BatchScrapeResponse',
    'ErrorResponse',
    'ScrapingError',
    'ValidationError',
    'ContentProcessingError',
    'NetworkError',
    'TimeoutError'
]
"""Request models for scraping operations."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, validator, Field


class ScrapeRequest(BaseModel):
    """Single page scraping request model."""

    url: HttpUrl = Field(..., description="URL to scrape")
    wait_time: Optional[int] = Field(5, ge=1, le=30, description="Wait time in seconds")
    headless: Optional[bool] = Field(True, description="Run browser in headless mode")
    include_title: Optional[bool] = Field(True, description="Include page title in response")
    remove_elements: Optional[List[str]] = Field(None, description="CSS selectors to remove")
    extract_metadata: Optional[bool] = Field(False, description="Extract page metadata")
    output_format: Optional[str] = Field("markdown", pattern="^(markdown|html|both)$")

    @validator('remove_elements')
    def validate_remove_elements(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate CSS selectors."""
        if v is None:
            return v

        # Basic CSS selector validation
        for selector in v:
            if not selector or not isinstance(selector, str):
                raise ValueError(f"Invalid CSS selector: {selector}")
            if len(selector) > 100:  # Reasonable limit
                raise ValueError(f"CSS selector too long: {selector}")

        return v

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            HttpUrl: str
        }
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "wait_time": 5,
                "headless": True,
                "include_title": True,
                "remove_elements": [".sidebar", ".ads"],
                "extract_metadata": True,
                "output_format": "markdown"
            }
        }


class BatchScrapeRequest(BaseModel):
    """Batch scraping request model."""

    urls: List[HttpUrl] = Field(..., min_items=1, max_items=50, description="URLs to scrape")
    wait_time: Optional[int] = Field(5, ge=1, le=30, description="Wait time in seconds")
    headless: Optional[bool] = Field(True, description="Run browser in headless mode")
    include_title: Optional[bool] = Field(True, description="Include page titles")
    remove_elements: Optional[List[str]] = Field(None, description="CSS selectors to remove")
    extract_metadata: Optional[bool] = Field(False, description="Extract page metadata")
    output_format: Optional[str] = Field("markdown", pattern="^(markdown|html|both)$")
    max_concurrent: Optional[int] = Field(3, ge=1, le=10, description="Max concurrent requests")
    delay_between_requests: Optional[float] = Field(1.0, ge=0.1, le=10.0, description="Delay between requests")

    @validator('urls')
    def validate_urls(cls, v: List[HttpUrl]) -> List[HttpUrl]:
        """Validate URLs list."""
        unique_urls = list(set(str(url) for url in v))
        if len(unique_urls) != len(v):
            raise ValueError("Duplicate URLs found in request")
        return v

    @validator('remove_elements')
    def validate_remove_elements(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate CSS selectors."""
        if v is None:
            return v

        for selector in v:
            if not selector or not isinstance(selector, str):
                raise ValueError(f"Invalid CSS selector: {selector}")
            if len(selector) > 100:
                raise ValueError(f"CSS selector too long: {selector}")

        return v

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            HttpUrl: str
        }
        json_schema_extra = {
            "example": {
                "urls": [
                    "https://example.com/article1",
                    "https://example.com/article2"
                ],
                "wait_time": 5,
                "headless": True,
                "include_title": True,
                "remove_elements": [".sidebar", ".ads"],
                "extract_metadata": True,
                "output_format": "markdown",
                "max_concurrent": 3,
                "delay_between_requests": 1.0
            }
        }


@dataclass
class ScrapingOptions:
    """Internal scraping options data class."""

    wait_time: int = 5
    headless: bool = True
    include_title: bool = True
    remove_elements: Optional[List[str]] = None
    extract_metadata: bool = False
    output_format: str = "markdown"
    max_concurrent: int = 3
    delay_between_requests: float = 1.0

    @classmethod
    def from_request(cls, request: ScrapeRequest) -> 'ScrapingOptions':
        """Create options from single scrape request."""
        return cls(
            wait_time=request.wait_time or 5,
            headless=request.headless if request.headless is not None else True,
            include_title=request.include_title if request.include_title is not None else True,
            remove_elements=request.remove_elements,
            extract_metadata=request.extract_metadata or False,
            output_format=request.output_format or "markdown"
        )

    @classmethod
    def from_batch_request(cls, request: BatchScrapeRequest) -> 'ScrapingOptions':
        """Create options from batch scrape request."""
        return cls(
            wait_time=request.wait_time or 5,
            headless=request.headless if request.headless is not None else True,
            include_title=request.include_title if request.include_title is not None else True,
            remove_elements=request.remove_elements,
            extract_metadata=request.extract_metadata or False,
            output_format=request.output_format or "markdown",
            max_concurrent=request.max_concurrent or 3,
            delay_between_requests=request.delay_between_requests or 1.0
        )
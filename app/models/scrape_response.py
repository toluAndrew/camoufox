"""Response models for scraping operations."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class PageMetadata(BaseModel):
    """Page metadata model."""

    description: Optional[str] = None
    keywords: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    canonical_url: Optional[str] = None
    language: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "description": "A comprehensive guide to web scraping",
                "keywords": "web scraping, python, automation",
                "author": "John Doe",
                "published_date": "2024-01-15T10:30:00Z",
                "canonical_url": "https://example.com/guide",
                "language": "en"
            }
        }


class ScrapeResponse(BaseModel):
    """Single page scraping response model."""

    success: bool = Field(..., description="Whether scraping was successful")
    url: str = Field(..., description="URL that was scraped")
    title: Optional[str] = Field(None, description="Page title")
    content: Optional[str] = Field(None, description="Scraped content")
    html: Optional[str] = Field(None, description="Raw HTML content")
    metadata: Optional[PageMetadata] = Field(None, description="Page metadata")
    length: Optional[int] = Field(None, description="Content length in characters")
    word_count: Optional[int] = Field(None, description="Word count")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Scraping timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[str] = Field(None, description="Error type classification")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "url": "https://example.com/article",
                "title": "Example Article",
                "content": "# Example Article\n\nThis is the content...",
                "metadata": {
                    "description": "An example article",
                    "author": "Jane Smith"
                },
                "length": 1500,
                "word_count": 250,
                "processing_time": 2.34,
                "timestamp": "2024-01-15T10:30:00.000Z"
            }
        }


class BatchScrapeResponse(BaseModel):
    """Batch scraping response model."""

    success: bool = Field(..., description="Whether batch operation was successful")
    total_urls: int = Field(..., description="Total number of URLs processed")
    successful_scrapes: int = Field(..., description="Number of successful scrapes")
    failed_scrapes: int = Field(..., description="Number of failed scrapes")
    results: List[ScrapeResponse] = Field(..., description="Individual scraping results")
    processing_time: float = Field(..., description="Total processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Batch operation timestamp")

    # Summary statistics
    total_words: Optional[int] = Field(None, description="Total words scraped")
    total_content_length: Optional[int] = Field(None, description="Total content length")
    average_processing_time: Optional[float] = Field(None, description="Average processing time per URL")

    def __init__(self, **data):
        """Initialize with computed statistics."""
        super().__init__(**data)

        # Calculate summary statistics
        successful_results = [r for r in self.results if r.success]

        if successful_results:
            self.total_words = sum(r.word_count or 0 for r in successful_results)
            self.total_content_length = sum(r.length or 0 for r in successful_results)

            processing_times = [r.processing_time for r in self.results if r.processing_time]
            if processing_times:
                self.average_processing_time = sum(processing_times) / len(processing_times)

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "total_urls": 5,
                "successful_scrapes": 4,
                "failed_scrapes": 1,
                "processing_time": 12.5,
                "total_words": 1250,
                "total_content_length": 7500,
                "average_processing_time": 2.5,
                "timestamp": "2024-01-15T10:30:00.000Z",
                "results": [
                    {
                        "success": True,
                        "url": "https://example.com/article1",
                        "title": "First Article",
                        "content": "Content here...",
                        "length": 1000,
                        "word_count": 150,
                        "processing_time": 2.1
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "Invalid URL provided",
                "error_type": "ValidationError",
                "error_code": "INVALID_URL",
                "details": {
                    "url": "not-a-valid-url",
                    "field": "url"
                },
                "timestamp": "2024-01-15T10:30:00.000Z",
                "request_id": "req_123456789"
            }
        }


@dataclass
class ScrapingResult:
    """Internal scraping result data class."""

    success: bool
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    html: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    length: Optional[int] = None
    word_count: Optional[int] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

    def to_response(self) -> ScrapeResponse:
        """Convert to response model."""
        metadata_obj = None
        if self.metadata:
            metadata_obj = PageMetadata(**self.metadata)

        return ScrapeResponse(
            success=self.success,
            url=self.url,
            title=self.title,
            content=self.content,
            html=self.html,
            metadata=metadata_obj,
            length=self.length,
            word_count=self.word_count,
            processing_time=self.processing_time,
            timestamp=datetime.utcnow().isoformat(),  # Convert to string
            error=self.error,
            error_type=self.error_type
        )
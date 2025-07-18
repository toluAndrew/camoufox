"""Custom exceptions for the web scraper service."""

from typing import Optional, Dict, Any


class ScrapingError(Exception):
    """Base exception for scraping operations."""

    def __init__(
            self,
            message: str,
            error_code: Optional[str] = None,
            details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.error_type = self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            'error': self.message,
            'error_type': self.error_type,
            'error_code': self.error_code,
            'details': self.details
        }


class ValidationError(ScrapingError):
    """Exception raised for validation errors."""

    def __init__(
            self,
            message: str,
            field: Optional[str] = None,
            value: Optional[Any] = None
    ) -> None:
        details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)

        super().__init__(
            message=message,
            error_code='VALIDATION_ERROR',
            details=details
        )


class NetworkError(ScrapingError):
    """Exception raised for network-related errors."""

    def __init__(
            self,
            message: str,
            url: Optional[str] = None,
            status_code: Optional[int] = None
    ) -> None:
        details = {}
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code

        super().__init__(
            message=message,
            error_code='NETWORK_ERROR',
            details=details
        )


class TimeoutError(ScrapingError):
    """Exception raised for timeout errors."""

    def __init__(
            self,
            message: str,
            url: Optional[str] = None,
            timeout_seconds: Optional[int] = None
    ) -> None:
        details = {}
        if url:
            details['url'] = url
        if timeout_seconds:
            details['timeout_seconds'] = timeout_seconds

        super().__init__(
            message=message,
            error_code='TIMEOUT_ERROR',
            details=details
        )


class ContentProcessingError(ScrapingError):
    """Exception raised for content processing errors."""

    def __init__(
            self,
            message: str,
            url: Optional[str] = None,
            processing_stage: Optional[str] = None
    ) -> None:
        details = {}
        if url:
            details['url'] = url
        if processing_stage:
            details['processing_stage'] = processing_stage

        super().__init__(
            message=message,
            error_code='CONTENT_PROCESSING_ERROR',
            details=details
        )


class BrowserError(ScrapingError):
    """Exception raised for browser-related errors."""

    def __init__(
            self,
            message: str,
            url: Optional[str] = None,
            browser_error: Optional[str] = None
    ) -> None:
        details = {}
        if url:
            details['url'] = url
        if browser_error:
            details['browser_error'] = browser_error

        super().__init__(
            message=message,
            error_code='BROWSER_ERROR',
            details=details
        )


class RateLimitError(ScrapingError):
    """Exception raised when rate limits are exceeded."""

    def __init__(
            self,
            message: str,
            retry_after: Optional[int] = None,
            current_rate: Optional[str] = None
    ) -> None:
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
        if current_rate:
            details['current_rate'] = current_rate

        super().__init__(
            message=message,
            error_code='RATE_LIMIT_ERROR',
            details=details
        )


class ConfigurationError(ScrapingError):
    """Exception raised for configuration errors."""

    def __init__(
            self,
            message: str,
            config_key: Optional[str] = None
    ) -> None:
        details = {}
        if config_key:
            details['config_key'] = config_key

        super().__init__(
            message=message,
            error_code='CONFIGURATION_ERROR',
            details=details
        )
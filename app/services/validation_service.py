"""Validation service for URLs and input data."""

import re
from urllib.parse import urlparse, urlunparse
from typing import List, Set, Optional
import logging

from ..models.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating URLs and input data."""

    def __init__(self) -> None:
        """Initialize the validation service."""
        # Common dangerous/blocked domains (can be extended)
        self.blocked_domains: Set[str] = {
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1'
        }

        # Allowed URL schemes
        self.allowed_schemes: Set[str] = {'http', 'https'}

        # Blocked file extensions
        self.blocked_extensions: Set[str] = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.tar', '.gz', '.exe', '.dmg', '.pkg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flv'
        }

        # URL pattern for basic validation
        self.url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and safe to scrape.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid and safe
        """
        try:
            return self._validate_url_format(url) and self._validate_url_safety(url)
        except Exception as e:
            logger.warning(f"Error validating URL {url}: {str(e)}")
            return False

    def validate_url_strict(self, url: str) -> None:
        """Strict URL validation that raises exceptions.

        Args:
            url: URL to validate

        Raises:
            ValidationError: If URL is invalid
        """
        if not isinstance(url, str):
            raise ValidationError("URL must be a string", field="url", value=url)

        if not url.strip():
            raise ValidationError("URL cannot be empty", field="url", value=url)

        if len(url) > 2048:  # Common URL length limit
            raise ValidationError("URL too long (max 2048 characters)", field="url", value=url)

        if not self._validate_url_format(url):
            raise ValidationError(f"Invalid URL format: {url}", field="url", value=url)

        if not self._validate_url_safety(url):
            raise ValidationError(f"URL not allowed for scraping: {url}", field="url", value=url)

    def validate_urls_batch(self, urls: List[str]) -> List[str]:
        """Validate a batch of URLs and return valid ones.

        Args:
            urls: List of URLs to validate

        Returns:
            List of valid URLs

        Raises:
            ValidationError: If no valid URLs found
        """
        if not urls:
            raise ValidationError("URL list cannot be empty", field="urls")

        if len(urls) > 100:  # Reasonable batch limit
            raise ValidationError("Too many URLs in batch (max 100)", field="urls")

        valid_urls = []
        invalid_urls = []

        for url in urls:
            try:
                self.validate_url_strict(url)
                valid_urls.append(url)
            except ValidationError as e:
                invalid_urls.append({"url": url, "error": str(e)})

        if not valid_urls:
            raise ValidationError(
                f"No valid URLs found in batch",
                field="urls",
                value={"invalid_count": len(invalid_urls), "examples": invalid_urls[:3]}
            )

        if invalid_urls:
            logger.warning(f"Found {len(invalid_urls)} invalid URLs in batch")

        return valid_urls

    def validate_css_selector(self, selector: str) -> bool:
        """Validate CSS selector for safety.

        Args:
            selector: CSS selector to validate

        Returns:
            True if selector is safe to use
        """
        if not selector or not isinstance(selector, str):
            return False

        # Basic length check
        if len(selector) > 200:
            return False

        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'javascript:',
            r'eval\(',
            r'<script',
            r'</script>',
            r'onclick=',
            r'onerror=',
            r'onload='
        ]

        selector_lower = selector.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, selector_lower):
                return False

        # Basic CSS selector pattern check
        css_pattern = re.compile(r'^[a-zA-Z0-9\s\.\#\[\]\:\-_,>+~*="\'()]+$')
        return bool(css_pattern.match(selector))

    def validate_css_selectors(self, selectors: List[str]) -> List[str]:
        """Validate list of CSS selectors.

        Args:
            selectors: List of CSS selectors to validate

        Returns:
            List of valid selectors

        Raises:
            ValidationError: If validation fails
        """
        if not selectors:
            return []

        if len(selectors) > 50:  # Reasonable limit
            raise ValidationError("Too many CSS selectors (max 50)", field="remove_elements")

        valid_selectors = []

        for selector in selectors:
            if self.validate_css_selector(selector):
                valid_selectors.append(selector)
            else:
                logger.warning(f"Invalid CSS selector ignored: {selector}")

        return valid_selectors

    def _validate_url_format(self, url: str) -> bool:
        """Validate URL format using regex and urlparse.

        Args:
            url: URL to validate

        Returns:
            True if format is valid
        """
        try:
            # Basic regex check
            if not self.url_pattern.match(url):
                return False

            # Parse URL components
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in self.allowed_schemes:
                return False

            # Check if netloc exists
            if not parsed.netloc:
                return False

            # Check for blocked file extensions
            path = parsed.path.lower()
            for ext in self.blocked_extensions:
                if path.endswith(ext):
                    return False

            return True

        except Exception:
            return False

    def _validate_url_safety(self, url: str) -> bool:
        """Check if URL is safe to scrape.

        Args:
            url: URL to check

        Returns:
            True if URL is safe
        """
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return False

            # Check blocked domains
            if hostname.lower() in self.blocked_domains:
                return False

            # Check for private IP ranges (basic check)
            if self._is_private_ip(hostname):
                return False

            # Check for suspicious patterns
            suspicious_patterns = [
                'admin',
                'login',
                'secure',
                'private',
                'internal'
            ]

            url_lower = url.lower()
            for pattern in suspicious_patterns:
                if pattern in hostname.lower() or f'/{pattern}' in url_lower:
                    logger.warning(f"Potentially suspicious URL pattern: {pattern} in {url}")

            return True

        except Exception:
            return False

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname is a private IP address.

        Args:
            hostname: Hostname to check

        Returns:
            True if it's a private IP
        """
        try:
            # Simple check for common private IP patterns
            private_patterns = [
                r'^10\.',
                r'^172\.1[6-9]\.',
                r'^172\.2[0-9]\.',
                r'^172\.3[0-1]\.',
                r'^192\.168\.',
                r'^127\.',
                r'^0\.',
                r'^169\.254\.'
            ]

            for pattern in private_patterns:
                if re.match(pattern, hostname):
                    return True

            return False

        except Exception:
            return False

    def get_domain_from_url(self, url: str) -> Optional[str]:
        """Extract domain from URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain name or None if invalid
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() if parsed.netloc else None
        except Exception:
            return None

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and unnecessary components.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        try:
            parsed = urlparse(url.strip())

            # Remove fragment
            normalized = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path,
                parsed.params,
                parsed.query,
                None  # Remove fragment
            ))

            return normalized

        except Exception:
            return url
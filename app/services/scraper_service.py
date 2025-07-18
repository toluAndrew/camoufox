"""Core scraping service with business logic."""

import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import logging

from camoufox.sync_api import Camoufox

from ..models.scrape_request import ScrapingOptions
from ..models.scrape_response import ScrapingResult
from ..models.exceptions import (
    NetworkError,
    TimeoutError,
    BrowserError,
    ContentProcessingError,
    ValidationError
)
from ..config import ScrapingConfig
from .content_processor import ContentProcessor
from .validation_service import ValidationService

logger = logging.getLogger(__name__)


class ScraperService:
    """Service class for web scraping operations."""

    def __init__(
            self,
            config: ScrapingConfig,
            content_processor: ContentProcessor,
            validation_service: ValidationService
    ) -> None:
        """Initialize the scraper service.

        Args:
            config: Scraping configuration
            content_processor: Content processing service
            validation_service: URL validation service
        """
        self.config = config
        self.content_processor = content_processor
        self.validation_service = validation_service
        self._executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)

    def scrape_single(self, url: str, options: ScrapingOptions) -> ScrapingResult:
        """Scrape a single URL.

        Args:
            url: URL to scrape
            options: Scraping options

        Returns:
            ScrapingResult with scraped data or error information
        """
        start_time = time.time()

        try:
            # Validate URL
            if not self.validation_service.is_valid_url(url):
                raise ValidationError(f"Invalid URL: {url}", field="url", value=url)

            logger.info(f"Starting scrape for: {url}")

            # Perform scraping
            result = self._scrape_page(url, options)

            # Calculate processing time
            processing_time = time.time() - start_time
            result.processing_time = processing_time

            logger.info(f"Successfully scraped {url} in {processing_time:.2f}s")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error scraping {url}: {str(e)}")

            return ScrapingResult(
                success=False,
                url=url,
                error=str(e),
                error_type=type(e).__name__,
                processing_time=processing_time
            )

    def scrape_batch(self, urls: List[str], options: ScrapingOptions) -> List[ScrapingResult]:
        """Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            options: Scraping options

        Returns:
            List of ScrapingResult objects
        """
        logger.info(f"Starting batch scrape for {len(urls)} URLs")
        start_time = time.time()

        results = []

        # Process URLs in batches to control concurrency
        batch_size = min(options.max_concurrent, len(urls))

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.scrape_single, url, options): url
                for url in urls
            }

            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Add delay between requests if specified
                    if options.delay_between_requests > 0:
                        time.sleep(options.delay_between_requests)

                except Exception as e:
                    logger.error(f"Error in batch processing for {url}: {str(e)}")
                    results.append(ScrapingResult(
                        success=False,
                        url=url,
                        error=str(e),
                        error_type=type(e).__name__
                    ))

        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        logger.info(f"Batch scrape completed: {successful}/{len(urls)} successful in {total_time:.2f}s")

        return results

    def _scrape_page(self, url: str, options: ScrapingOptions) -> ScrapingResult:
        """Internal method to scrape a single page.

        Args:
            url: URL to scrape
            options: Scraping options

        Returns:
            ScrapingResult with scraped data

        Raises:
            NetworkError: For network-related issues
            BrowserError: For browser-related issues
            ContentProcessingError: For content processing issues
        """
        try:
            with Camoufox(headless=options.headless,
     ) as browser:
                page = browser.new_page()

                # Set up request blocking for media resources
                def block_media(route, request):
                    if request.resource_type in ["image", "media", "font"]:
                        return route.abort()
                    return route.continue_()

                page.route("**/*", block_media)

                try:
                    # Navigate to page with timeout
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        # timeout=options.wait_time * 1000  # Convert to milliseconds
                    )

                    # Wait for any additional content to load
                    # time.sleep(min(options.wait_time, self.config.max_wait_time))

                    # Extract page data
                    title = page.title() if options.include_title else ""

                    # # Remove unwanted elements
                    # if options.remove_elements:
                    #     self._remove_elements(page, options.remove_elements)
                    #
                    # # Remove default unwanted elements
                    # self._remove_default_elements(page)

                    # Get HTML content
                    html_content = page.content()

                    print("content grabbed")

                    # Process content
                    processed_content = self.content_processor.process_content(
                        html_content=html_content,
                        title=title,
                        output_format=options.output_format
                    )

                    # Extract metadata if requested
                    metadata = None
                    # if options.extract_metadata:
                    #     metadata = self._extract_metadata(page)

                    # Calculate content statistics
                    content_length = len(processed_content.get('content', ''))
                    word_count = len(processed_content.get('content', '').split())

                    return ScrapingResult(
                        success=True,
                        url=url,
                        title=title,
                        content=processed_content.get('content'),
                        html=processed_content.get('html') if options.output_format in ['html', 'both'] else None,
                        metadata=metadata,
                        length=content_length,
                        word_count=word_count
                    )

                except Exception as e:
                    if "timeout" in str(e).lower():
                        raise TimeoutError(f"Page load timeout for {url}", url=url, timeout_seconds=options.wait_time)
                    elif "net::" in str(e) or "DNS" in str(e):
                        raise NetworkError(f"Network error accessing {url}: {str(e)}", url=url)
                    else:
                        raise BrowserError(f"Browser error for {url}: {str(e)}", url=url, browser_error=str(e))

        except (NetworkError, TimeoutError, BrowserError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Wrap unknown exceptions
            raise BrowserError(f"Unexpected error scraping {url}: {str(e)}", url=url, browser_error=str(e))

    def _remove_elements(self, page, selectors: List[str]) -> None:
        """Remove elements by CSS selectors.

        Args:
            page: Browser page object
            selectors: List of CSS selectors to remove
        """
        for selector in selectors:
            try:
                page.evaluate(f"""
                    document.querySelectorAll('{selector}').forEach(el => el.remove())
                """)
                logger.debug(f"Removed elements: {selector}")
            except Exception as e:
                logger.warning(f"Could not remove elements with selector '{selector}': {str(e)}")

    def _remove_default_elements(self, page) -> None:
        """Remove common unwanted elements.

        Args:
            page: Browser page object
        """
        if self.config.default_remove_elements:
            self._remove_elements(page, self.config.default_remove_elements)

    def _extract_metadata(self, page) -> Dict[str, Any]:
        """Extract metadata from the page.

        Args:
            page: Browser page object

        Returns:
            Dictionary containing extracted metadata
        """
        metadata = {}

        try:
            # Meta description
            try:
                desc = page.locator('meta[name="description"]').get_attribute('content')
                if desc:
                    metadata['description'] = desc
            except:
                pass

            # Meta keywords
            try:
                keywords = page.locator('meta[name="keywords"]').get_attribute('content')
                if keywords:
                    metadata['keywords'] = keywords
            except:
                pass

            # Author
            try:
                author = page.locator('meta[name="author"]').get_attribute('content')
                if author:
                    metadata['author'] = author
            except:
                pass

            # Published date (try multiple selectors)
            try:
                selectors = [
                    'meta[property="article:published_time"]',
                    'meta[name="publication_date"]',
                    'meta[name="date"]',
                    'time[datetime]'
                ]

                for selector in selectors:
                    try:
                        date_elem = page.locator(selector).first
                        if date_elem:
                            date_value = date_elem.get_attribute('content') or date_elem.get_attribute('datetime')
                            if date_value:
                                metadata['published_date'] = date_value
                                break
                    except:
                        continue
            except:
                pass

            # Canonical URL
            try:
                canonical = page.locator('link[rel="canonical"]').get_attribute('href')
                if canonical:
                    metadata['canonical_url'] = canonical
            except:
                pass

            # Language
            try:
                lang = page.locator('html').get_attribute('lang')
                if lang:
                    metadata['language'] = lang
            except:
                pass

        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")

        return metadata

    def __del__(self) -> None:
        """Cleanup resources."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
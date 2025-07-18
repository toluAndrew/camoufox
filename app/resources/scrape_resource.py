"""REST API resources for scraping operations."""

import time
import logging
from typing import Dict, Any
from flask import request
from flask_restful import Resource
from pydantic import ValidationError as PydanticValidationError

from ..models.scrape_request import ScrapeRequest, BatchScrapeRequest, ScrapingOptions
from ..models.scrape_response import (
    ScrapeResponse, BatchScrapeResponse, ErrorResponse,
    ScrapingResult
)
from ..models.exceptions import (
    ScrapingError, ValidationError, NetworkError,
    TimeoutError, ContentProcessingError
)
from ..services.scraper_service import ScraperService
from ..utils.decorators import handle_exceptions, log_request
from ..utils.validators import validate_json_payload

logger = logging.getLogger(__name__)


class ScrapeResource(Resource):
    """Resource for single URL scraping."""

    def __init__(self, scraper_service: ScraperService) -> None:
        """Initialize with scraper service dependency.

        Args:
            scraper_service: Injected scraper service
        """
        self.scraper_service = scraper_service

    @handle_exceptions
    @log_request
    def post(self) -> tuple[Dict[str, Any], int]:
        """Scrape a single URL.

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate JSON payload
            payload = validate_json_payload(request)

            # Parse and validate request
            scrape_request = ScrapeRequest(**payload)

            # Convert to scraping options
            options = ScrapingOptions.from_request(scrape_request)

            # Perform scraping
            result = self.scraper_service.scrape_single(
                url=str(scrape_request.url),
                options=options
            )

            # Convert to response model
            response = result.to_response()

            # Return appropriate status code
            status_code = 200 if response.success else 422

            logger.info(f"Scrape request completed for {scrape_request.url} with status {status_code}")

            return response.dict(), status_code

        except PydanticValidationError as e:
            logger.warning(f"Validation error in scrape request: {str(e)}")
            error_response = ErrorResponse(
                error="Invalid request data",
                error_type="ValidationError",
                error_code="INVALID_REQUEST",
                details={"validation_errors": e.errors()}
            )
            return error_response.dict(), 400

        except ValidationError as e:
            logger.warning(f"Custom validation error: {str(e)}")
            error_response = ErrorResponse(
                error=e.message,
                error_type=e.error_type,
                error_code=e.error_code,
                details=e.details
            )
            return error_response.dict(), 400

        except (NetworkError, TimeoutError) as e:
            logger.error(f"Network/timeout error: {str(e)}")
            error_response = ErrorResponse(
                error=e.message,
                error_type=e.error_type,
                error_code=e.error_code,
                details=e.details
            )
            return error_response.dict(), 422

        except ContentProcessingError as e:
            logger.error(f"Content processing error: {str(e)}")
            error_response = ErrorResponse(
                error=e.message,
                error_type=e.error_type,
                error_code=e.error_code,
                details=e.details
            )
            return error_response.dict(), 422

        except ScrapingError as e:
            logger.error(f"Scraping error: {str(e)}")
            error_response = ErrorResponse(
                error=e.message,
                error_type=e.error_type,
                error_code=e.error_code,
                details=e.details
            )
            return error_response.dict(), 500

        except Exception as e:
            logger.error(f"Unexpected error in scrape request: {str(e)}", exc_info=True)
            error_response = ErrorResponse(
                error="Internal server error occurred during scraping",
                error_type="InternalError",
                error_code="INTERNAL_ERROR",
                details={"original_error": str(e)}
            )
            return error_response.dict(), 500


class BatchScrapeResource(Resource):
    """Resource for batch URL scraping."""

    def __init__(self, scraper_service: ScraperService) -> None:
        """Initialize with scraper service dependency.

        Args:
            scraper_service: Injected scraper service
        """
        self.scraper_service = scraper_service

    @handle_exceptions
    @log_request
    def post(self) -> tuple[Dict[str, Any], int]:
        """Scrape multiple URLs in batch.

        Returns:
            Tuple of (response_data, status_code)
        """
        start_time = time.time()

        try:
            # Validate JSON payload
            payload = validate_json_payload(request)

            # Parse and validate request
            batch_request = BatchScrapeRequest(**payload)

            # Convert to scraping options
            options = ScrapingOptions.from_batch_request(batch_request)

            # Convert URLs to strings
            urls = [str(url) for url in batch_request.urls]

            logger.info(f"Starting batch scrape for {len(urls)} URLs")

            # Perform batch scraping
            results = self.scraper_service.scrape_batch(urls=urls, options=options)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Create batch response
            successful_count = sum(1 for r in results if r.success)
            failed_count = len(results) - successful_count

            # Convert results to response models
            response_results = [result.to_response() for result in results]

            batch_response = BatchScrapeResponse(
                success=True,  # Batch is successful if it completes, regardless of individual failures
                total_urls=len(urls),
                successful_scrapes=successful_count,
                failed_scrapes=failed_count,
                results=response_results,
                processing_time=processing_time
            )

            # Determine status code based on results
            if successful_count == len(urls):
                status_code = 200  # All successful
            elif successful_count > 0:
                status_code = 207  # Multi-status (partial success)
            else:
                status_code = 422  # All failed

            logger.info(
                f"Batch scrape completed: {successful_count}/{len(urls)} successful "
                f"in {processing_time:.2f}s"
            )

            return batch_response.dict(), status_code

        except PydanticValidationError as e:
            logger.warning(f"Validation error in batch scrape request: {str(e)}")
            error_response = ErrorResponse(
                error="Invalid request data",
                error_type="ValidationError",
                error_code="INVALID_REQUEST",
                details={"validation_errors": e.errors()}
            )
            return error_response.dict(), 400

        except ValidationError as e:
            logger.warning(f"Custom validation error: {str(e)}")
            error_response = ErrorResponse(
                error=e.message,
                error_type=e.error_type,
                error_code=e.error_code,
                details=e.details
            )
            return error_response.dict(), 400

        except ScrapingError as e:
            logger.error(f"Scraping error in batch: {str(e)}")
            error_response = ErrorResponse(
                error=e.message,
                error_type=e.error_type,
                error_code=e.error_code,
                details=e.details
            )
            return error_response.dict(), 500

        except Exception as e:
            logger.error(f"Unexpected error in batch scrape: {str(e)}", exc_info=True)
            error_response = ErrorResponse(
                error="Internal server error occurred during batch scraping",
                error_type="InternalError",
                error_code="INTERNAL_ERROR",
                details={"original_error": str(e)}
            )
            return error_response.dict(), 500


class ScrapeStatusResource(Resource):
    """Resource for checking scrape operation status."""

    def __init__(self, scraper_service: ScraperService) -> None:
        """Initialize with scraper service dependency.

        Args:
            scraper_service: Injected scraper service
        """
        self.scraper_service = scraper_service

    @handle_exceptions
    @log_request
    def get(self) -> tuple[Dict[str, Any], int]:
        """Get scraper service status and statistics.

        Returns:
            Tuple of (status_data, status_code)
        """
        try:
            # Get current timestamp
            current_time = datetime.utcnow().isoformat()

            # Basic service status
            status_data = {
                "service": "web_scraper",
                "status": "operational",
                "timestamp": current_time,
                "version": "1.0.0",
                "capabilities": {
                    "single_scrape": True,
                    "batch_scrape": True,
                    "max_concurrent": self.scraper_service.config.max_concurrent_requests,
                    "supported_formats": ["markdown", "html", "both"],
                    "metadata_extraction": True,
                    "custom_selectors": True
                },
                "limits": {
                    "max_concurrent_requests": self.scraper_service.config.max_concurrent_requests,
                    "max_wait_time": self.scraper_service.config.max_wait_time,
                    "request_timeout": self.scraper_service.config.request_timeout,
                    "max_batch_size": 50,
                    "max_url_length": 2048,
                    "max_content_length": 1000000
                }
            }

            return status_data, 200

        except Exception as e:
            logger.error(f"Error getting scraper status: {str(e)}", exc_info=True)
            error_response = ErrorResponse(
                error="Error retrieving service status",
                error_type="InternalError",
                error_code="STATUS_ERROR",
                details={"original_error": str(e)}
            )
            return error_response.dict(), 500
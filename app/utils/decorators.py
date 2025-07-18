"""Decorators for request handling and error management."""

import logging
from functools import wraps
from typing import Callable, Tuple, Any
from flask import request

from ..models.exceptions import ScrapingError
from ..models.scrape_response import ErrorResponse

logger = logging.getLogger(__name__)


def handle_exceptions(func: Callable) -> Callable:
    """Decorator to handle exceptions in resources.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function that handles exceptions
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[Any, int]:
        try:
            return func(*args, **kwargs)
        except ScrapingError as e:
            logger.error(f"Scraping error in {func.__name__}: {str(e)}")
            error_response = ErrorResponse(
                error=e.message,
                error_type=e.error_type,
                error_code=e.error_code,
                details=e.details
            )
            return error_response.dict(), 500
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            error_response = ErrorResponse(
                error="Internal server error",
                error_type="InternalError",
                error_code="INTERNAL_ERROR",
                details={"original_error": str(e)}
            )
            return error_response.dict(), 500

    return wrapper


def log_request(func: Callable) -> Callable:
    """Decorator to log incoming requests.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function that logs request details
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[Any, int]:
        logger.info(
            f"Received {request.method} request to {request.path} "
            f"from {request.remote_addr} with payload: {request.get_json(silent=True)}"
        )
        return func(*args, **kwargs)

    return wrapper
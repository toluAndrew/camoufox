"""Validation utilities for request payloads."""

import logging
from typing import Dict, Any
from flask import Request
from ..models.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_json_payload(request: Request) -> Dict[str, Any]:
    """Validate that the request contains a valid JSON payload.

    Args:
        request: Flask request object

    Returns:
        Parsed JSON payload as dictionary

    Raises:
        ValidationError: If payload is invalid or not JSON
    """
    if not request.is_json:
        logger.error("Request content type is not JSON")
        raise ValidationError(
            message="Request must be JSON",
            error_code="INVALID_CONTENT_TYPE",
            details={"content_type": request.content_type}
        )

    try:
        payload = request.get_json(silent=False)
        if not payload:
            logger.error("Empty JSON payload received")
            raise ValidationError(
                message="Empty JSON payload",
                error_code="EMPTY_PAYLOAD"
            )
        return payload
    except Exception as e:
        logger.error(f"Invalid JSON payload: {str(e)}")
        raise ValidationError(
            message="Invalid JSON payload",
            error_code="INVALID_JSON",
            details={"error": str(e)}
        )
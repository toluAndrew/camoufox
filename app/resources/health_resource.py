"""Health check resource for monitoring."""

import time
import logging
from typing import Dict, Any
from flask_restful import Resource

from ..models.exceptions import ScrapingError
from ..utils.decorators import handle_exceptions

logger = logging.getLogger(__name__)


class HealthResource(Resource):
    """Health check resource for service monitoring."""

    @handle_exceptions
    def get(self) -> tuple[Dict[str, Any], int]:
        """Perform health check.

        Returns:
            Tuple of (health_data, status_code)
        """
        try:
            current_time = time.time()

            # Basic health check data
            health_data = {
                "status": "healthy",
                "timestamp": current_time,
                "service": "web_scraper_service",
                "version": "1.0.0",
                "uptime": current_time,  # In production, this would be actual uptime
                "checks": {
                    "api": "ok",
                    "dependencies": "ok"
                }
            }

            # Perform basic dependency checks
            try:
                # Test imports of key dependencies
                import camoufox
                import html2text
                import pydantic
                health_data["checks"]["camoufox"] = "ok"
                health_data["checks"]["html2text"] = "ok"
                health_data["checks"]["pydantic"] = "ok"

            except ImportError as e:
                logger.error(f"Dependency check failed: {str(e)}")
                health_data["status"] = "degraded"
                health_data["checks"]["dependencies"] = f"error: {str(e)}"
                return health_data, 503

            return health_data, 200

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)

            error_health_data = {
                "status": "unhealthy",
                "timestamp": time.time(),
                "service": "web_scraper_service",
                "error": str(e),
                "checks": {
                    "api": "error"
                }
            }

            return error_health_data, 503


class ReadinessResource(Resource):
    """Readiness check resource for Kubernetes-style health checks."""

    @handle_exceptions
    def get(self) -> tuple[Dict[str, Any], int]:
        """Check if service is ready to serve requests.

        Returns:
            Tuple of (readiness_data, status_code)
        """
        try:
            # Perform more thorough readiness checks
            readiness_checks = {}
            all_ready = True

            # Check critical dependencies
            try:
                from camoufox.sync_api import Camoufox
                readiness_checks["camoufox"] = "ready"
            except Exception as e:
                readiness_checks["camoufox"] = f"not ready: {str(e)}"
                all_ready = False

            try:
                import html2text
                converter = html2text.HTML2Text()
                readiness_checks["html2text"] = "ready"
            except Exception as e:
                readiness_checks["html2text"] = f"not ready: {str(e)}"
                all_ready = False

            # Basic configuration check
            try:
                from ..config import get_config
                config = get_config()
                readiness_checks["configuration"] = "ready"
            except Exception as e:
                readiness_checks["configuration"] = f"not ready: {str(e)}"
                all_ready = False

            readiness_data = {
                "status": "ready" if all_ready else "not ready",
                "timestamp": time.time(),
                "service": "web_scraper_service",
                "checks": readiness_checks
            }

            status_code = 200 if all_ready else 503
            return readiness_data, status_code

        except Exception as e:
            logger.error(f"Readiness check failed: {str(e)}", exc_info=True)

            error_readiness_data = {
                "status": "not ready",
                "timestamp": time.time(),
                "service": "web_scraper_service",
                "error": str(e),
                "checks": {
                    "api": "error"
                }
            }

            return error_readiness_data, 503


class LivenessResource(Resource):
    """Liveness check resource for Kubernetes-style health checks."""

    @handle_exceptions
    def get(self) -> tuple[Dict[str, Any], int]:
        """Check if service is alive and responsive.

        Returns:
            Tuple of (liveness_data, status_code)
        """
        try:
            # Simple liveness check - if we can respond, we're alive
            liveness_data = {
                "status": "alive",
                "timestamp": time.time(),
                "service": "web_scraper_service"
            }

            return liveness_data, 200

        except Exception as e:
            logger.error(f"Liveness check failed: {str(e)}", exc_info=True)

            error_liveness_data = {
                "status": "dead",
                "timestamp": time.time(),
                "service": "web_scraper_service",
                "error": str(e)
            }

            return error_liveness_data, 503
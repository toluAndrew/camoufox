"""Flask application factory."""

from flask import Flask
from flask_restful import Api  # Add this import
from typing import Optional
from .config import get_config, AppConfig
from .utils.logger import setup_logging
from .extensions import init_extensions
from .services import ScraperService, ContentProcessor, ValidationService
from .resources import (
    ScrapeResource, BatchScrapeResource, ScrapeStatusResource,
    HealthResource, ReadinessResource, LivenessResource
)


def create_app(config: Optional[AppConfig] = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config: Optional configuration object, defaults to environment-based config

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Load configuration
    config = config or get_config()
    app.config.from_object(config)

    # Setup logging
    setup_logging(config)

    # Initialize extensions
    init_extensions(app)

    # Initialize Flask-RESTful API
    api = Api(app)

    # Initialize services
    validation_service = ValidationService()
    content_processor = ContentProcessor(config.content_processing)
    scraper_service = ScraperService(config.scraping, content_processor, validation_service)

    # Register API resources
    api.add_resource(ScrapeResource, '/api/v1/scrape', resource_class_args=(scraper_service,))
    api.add_resource(BatchScrapeResource, '/api/v1/scrape/batch', resource_class_args=(scraper_service,))
    api.add_resource(ScrapeStatusResource, '/api/v1/scrape/status', resource_class_args=(scraper_service,))
    api.add_resource(HealthResource, '/api/v1/health')
    api.add_resource(ReadinessResource, '/api/v1/readiness')
    api.add_resource(LivenessResource, '/api/v1/liveness')

    # Basic route for root
    @app.route('/')
    def index():
        return {
            'service': 'web_scraper_service',
            'version': config.API_VERSION,
            'status': 'running'
        }, 200

    return app
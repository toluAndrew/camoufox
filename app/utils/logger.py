"""Logging configuration and utilities."""

import logging
import logging.config
import sys
import os
from typing import Dict, Any

from ..config import AppConfig


def setup_logging(config: AppConfig) -> None:
    """Set up application logging configuration.

    Args:
        config: Application configuration with logging settings
    """
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': config.LOG_FORMAT,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': config.LOG_LEVEL,
                'formatter': 'standard',
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': config.LOG_LEVEL,
                'formatter': 'detailed',
                'filename': 'logs/app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': 'logs/error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file', 'error_file'],
                'level': config.LOG_LEVEL,
                'propagate': False
            },
            'web_scraper_service': {
                'handlers': ['console', 'file', 'error_file'],
                'level': config.LOG_LEVEL,
                'propagate': False
            }
        }
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized")
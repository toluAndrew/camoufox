"""Flask extensions and shared resources."""

from flask_cors import CORS
from typing import Optional

cors: Optional[CORS] = None


def init_extensions(app):
    """Initialize Flask extensions.

    Args:
        app: Flask application instance
    """
    global cors
    cors = CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
"""Development server entry point."""

from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])

# source venv/bin/activate

# https://www.nbcnews.com/business/business-news/trump-threatens-25-tariff-apple-not-start-making-iphones-america-rcna208709
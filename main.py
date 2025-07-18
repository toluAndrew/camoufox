import time
import html2text
import re
import logging
from camoufox.sync_api import Camoufox
from urllib.parse import urlparse
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class WebPageScraper:
    def __init__(self, wait_time=5, headless=True):
        self.wait_time = wait_time
        self.headless = headless
        self.html2text = html2text.HTML2Text()
        self._configure_markdown_converter()

    def _configure_markdown_converter(self):
        """Configure the HTML to Markdown converter"""
        self.html2text.ignore_links = True
        self.html2text.ignore_images = True
        self.html2text.body_width = 0  # No line wrapping
        self.html2text.unicode_snob = True
        self.html2text.ignore_emphasis = False
        self.html2text.skip_internal_links = True

    def scrape_page(self, url, remove_elements=None, include_title=True):
        """
        Scrape a single page and return structured data

        Args:
            url (str): URL to scrape
            remove_elements (list): CSS selectors of elements to remove
            include_title (bool): Whether to include page title

        Returns:
            dict: Contains title, html, markdown, and metadata
        """
        logger.info(f"Scraping: {url}")

        # Validate URL
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")

        with Camoufox(headless=self.headless) as browser:
            page = browser.new_page()

            # Block media resources
            def block_media(route, request):
                if request.resource_type in ["image", "media", "font"]:
                    return route.abort()
                return route.continue_()

            page.route("**/*", block_media)

            try:
                page.goto(url, wait_until="domcontentloaded")

                # Get page title
                title = page.title() if include_title else ""

                # Optional: Remove specified elements
                # if remove_elements:
                #     self._remove_elements(page, remove_elements)

                # Optional: Remove default unwanted elements
                # self._remove_default_elements(page)

                # Get content
                html_content = page.content()

                # Convert to markdown
                markdown = self._html_to_markdown(html_content, title)

                # Optional: Extract metadata
                # metadata = self._extract_metadata(page)

                return {
                    'success': True,
                    'url': url,
                    'title': title,
                    'html': html_content,
                    'markdown': markdown,
                    # 'metadata': metadata,
                    'length': len(markdown),
                    'word_count': len(markdown.split())
                }

            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                return {
                    'success': False,
                    'url': url,
                    'error': str(e)
                }

    def scrape_multiple(self, urls, remove_elements=None, include_title=True):
        """
        Scrape multiple URLs

        Args:
            urls (list): List of URLs to scrape
            remove_elements (list): CSS selectors of elements to remove
            include_title (bool): Whether to include page titles

        Returns:
            list: List of scraping results
        """
        results = []

        for i, url in enumerate(urls, 1):
            logger.info(f"Processing {i}/{len(urls)}: {url}")
            result = self.scrape_page(url, remove_elements, include_title)
            results.append(result)

            # Small delay between requests to be respectful
            if i < len(urls):
                time.sleep(1)

        return results

    def _is_valid_url(self, url):
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _remove_elements(self, page, selectors):
        """Remove elements by CSS selectors"""
        for selector in selectors:
            try:
                page.evaluate(f"""
                    document.querySelectorAll('{selector}').forEach(el => el.remove())
                """)
                logger.debug(f"Removed elements: {selector}")
            except Exception as e:
                logger.warning(f"Could not remove {selector}: {e}")

    def _remove_default_elements(self, page):
        """Remove common unwanted elements"""
        default_selectors = [
            'script', 'style', 'noscript',
            'nav', 'header', 'footer',
            '.advertisement', '.ads', '.ad',
            '.social-share', '.social-sharing',
            '#comments', '.comments',
            '.sidebar', '.related-articles',
            '.newsletter-signup', '.popup',
            '.cookie-notice', '.gdpr-notice'
        ]
        self._remove_elements(page, default_selectors)

    def _html_to_markdown(self, html_content, title=""):
        """Convert HTML to clean markdown"""
        try:
            # Convert HTML to markdown
            markdown = self.html2text.handle(html_content)

            # Clean up the markdown
            markdown = self._clean_markdown(markdown)

            # Add title if provided
            if title:
                markdown = f"# {title}\n\n{markdown}"

            return markdown

        except Exception as e:
            logger.error(f"Error converting to markdown: {e}")
            return ""

    def _clean_markdown(self, markdown):
        """Clean up markdown formatting"""
        # Remove excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)

        # Remove trailing spaces
        markdown = re.sub(r' +\n', '\n', markdown)

        # Clean up empty links
        markdown = re.sub(r'\[\]\([^)]*\)', '', markdown)

        # Remove standalone brackets
        markdown = re.sub(r'^\[\]\s*$', '', markdown, flags=re.MULTILINE)

        # Clean up excessive dashes/underscores
        markdown = re.sub(r'^[-_]{3,}$', '---', markdown, flags=re.MULTILINE)

        # Remove empty headers
        markdown = re.sub(r'^#+\s*$', '', markdown, flags=re.MULTILINE)

        return markdown.strip()

    def _extract_metadata(self, page):
        """Extract useful metadata from the page"""
        try:
            metadata = {}

            # Get meta description
            try:
                desc = page.locator('meta[name="description"]').get_attribute('content')
                metadata['description'] = desc
            except:
                pass

            # Get meta keywords
            try:
                keywords = page.locator('meta[name="keywords"]').get_attribute('content')
                metadata['keywords'] = keywords
            except:
                pass

            # Get author
            try:
                author = page.locator('meta[name="author"]').get_attribute('content')
                metadata['author'] = author
            except:
                pass

            # Get published date
            try:
                date = page.locator('meta[property="article:published_time"]').get_attribute('content')
                metadata['published_date'] = date
            except:
                pass

            return metadata

        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
            return {}


# Utility functions for saving and loading results
def save_to_file(data, filename, format='json'):
    """Save scraping results to file"""
    filepath = Path(filename)

    if format == 'json':
        with open(filepath.with_suffix('.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    elif format == 'markdown':
        with open(filepath.with_suffix('.md'), 'w', encoding='utf-8') as f:
            if isinstance(data, dict) and 'markdown' in data:
                f.write(data['markdown'])
            elif isinstance(data, list):
                for item in data:
                    if item.get('success') and 'markdown' in item:
                        f.write(f"\n\n---\n\n{item['markdown']}")

    logger.info(f"Saved to: {filepath}")


def load_urls_from_file(filename):
    """Load URLs from a text file (one per line)"""
    with open(filename, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return urls


# Example usage functions
def scrape_single_example():
    """Example: Scrape a single page"""
    scraper = WebPageScraper(wait_time=5)

    url = "https://www.ig.com/ae/news-and-trade-ideas/AUD-USD1-250526"
    # url = "https://finance.yahoo.com/news/berkshire-hathaway-brk-b-low-141246592.html"
    result = scraper.scrape_page(
        url=url,
        remove_elements=['.sidebar', '.related-content'],  # Additional elements to remove
        include_title=True
    )

    if result['success']:
        print(f"Title: {result['title']}")
        print(f"Word count: {result['word_count']}")
        print(f"Markdown length: {result['length']}")
        print("\nFirst 500 characters of markdown:")
        print(result['markdown'] + "...")

        # Save results
        save_to_file(result, 'scraped_article', 'json')
        save_to_file(result, 'scraped_article', 'markdown')
    else:
        print(f"Error: {result['error']}")


def scrape_multiple_example():
    """Example: Scrape multiple pages"""
    scraper = WebPageScraper(wait_time=3)

    urls = [
        "https://www.marketwatch.com/story/apple-has-been-the-worst-big-tech-stock-lately-heres-why-investors-are-missing-the-big-picture-3fdfa582",
        "https://example.com/another-article"  # Add more URLs as needed
    ]

    results = scraper.scrape_multiple(urls, include_title=True)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"Successfully scraped: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        total_words = sum(r['word_count'] for r in successful)
        print(f"Total words scraped: {total_words}")

        # Save all results
        save_to_file(results, 'batch_scrape_results', 'json')
        save_to_file(successful, 'batch_scrape_content', 'markdown')


if __name__ == "__main__":
    # Run the single page example
    print("=== Single Page Scraping ===")
    scrape_single_example()

    print("\n=== Multiple Page Scraping ===")
    # scrape_multiple_example()  # Uncomment to test batch scraping
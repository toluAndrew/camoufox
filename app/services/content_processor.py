"""Content processing service for HTML to Markdown conversion."""

import re
import html2text
import logging
from typing import Dict, Any, Optional

from ..config import ContentProcessingConfig
from ..models.exceptions import ContentProcessingError

logger = logging.getLogger(__name__)


class ContentProcessor:
    """Service for processing and converting web content."""

    def __init__(self, config: ContentProcessingConfig) -> None:
        """Initialize the content processor.

        Args:
            config: Content processing configuration
        """
        self.config = config
        self.html2text = html2text.HTML2Text()
        self._configure_markdown_converter()

    def _configure_markdown_converter(self) -> None:
        """Configure the HTML to Markdown converter."""
        self.html2text.ignore_links = self.config.ignore_links
        self.html2text.ignore_images = self.config.ignore_images
        self.html2text.body_width = self.config.body_width
        self.html2text.unicode_snob = self.config.unicode_snob
        self.html2text.ignore_emphasis = self.config.ignore_emphasis
        self.html2text.skip_internal_links = self.config.skip_internal_links

    def process_content(
            self,
            html_content: str,
            title: str = "",
            output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """Process HTML content and convert to specified format.

        Args:
            html_content: Raw HTML content
            title: Page title to include
            output_format: Output format ('markdown', 'html', or 'both')

        Returns:
            Dictionary with processed content

        Raises:
            ContentProcessingError: If processing fails
        """
        try:
            # Validate content length
            if len(html_content) > self.config.max_content_length:
                raise ContentProcessingError(
                    f"Content too large: {len(html_content)} bytes (max: {self.config.max_content_length})",
                    processing_stage="validation"
                )

            result = {}

            # Process HTML if requested
            if output_format in ['html', 'both']:
                cleaned_html = self._clean_html(html_content)
                result['html'] = cleaned_html



            # Process Markdown if requested
            if output_format in ['markdown', 'both']:
                print("starting markdown generation")
                markdown_content = self._html_to_markdown(html_content, title)

                # Validate minimum content length
                if len(markdown_content.strip()) < self.config.min_content_length:
                    logger.warning(f"Content too short: {len(markdown_content)} characters")

                result['content'] = markdown_content
                print("markdown content generated")

            return result

        # except ContentProcessingError:
        #     # Re-raise content processing errors
        #     raise
        except Exception as e:
            raise ContentProcessingError(
                f"Error processing content: {str(e)}",
                processing_stage="conversion"
            )

    def _html_to_markdown(self, html_content: str, title: str = "") -> str:
        """Convert HTML to clean markdown.

        Args:
            html_content: Raw HTML content
            title: Page title to prepend

        Returns:
            Clean markdown content
        """
        try:
            # Convert HTML to markdown
            markdown = self.html2text.handle(html_content)

            # Clean up the markdown
            markdown = self._clean_markdown(markdown)

            # Add title if provided
            if title and title.strip():
                markdown = f"# {title.strip()}\n\n{markdown}"

            return markdown

        except Exception as e:
            raise ContentProcessingError(
                f"Error converting HTML to markdown: {str(e)}",
                processing_stage="html_to_markdown"
            )

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned HTML content
        """
        try:
            # Remove script and style tags
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

            # Remove comments
            html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)

            # Clean up excessive whitespace
            html_content = re.sub(r'\s+', ' ', html_content)
            html_content = re.sub(r'\n\s*\n', '\n', html_content)

            return html_content.strip()

        except Exception as e:
            raise ContentProcessingError(
                f"Error cleaning HTML: {str(e)}",
                processing_stage="html_cleaning"
            )

    def _clean_markdown(self, markdown: str) -> str:
        """Clean up markdown formatting.

        Args:
            markdown: Raw markdown content

        Returns:
            Cleaned markdown content
        """
        try:
            # Remove excessive newlines (more than 2)
            markdown = re.sub(r'\n{3,}', '\n\n', markdown)

            # Remove trailing spaces at end of lines
            markdown = re.sub(r' +\n', '\n', markdown)

            # Clean up empty links
            markdown = re.sub(r'\[\]\([^)]*\)', '', markdown)

            # Remove standalone empty brackets
            markdown = re.sub(r'^\[\]\s*$', '', markdown, flags=re.MULTILINE)

            # Clean up excessive dashes/underscores (convert to standard)
            markdown = re.sub(r'^[-_]{3,}$', '---', markdown, flags=re.MULTILINE)

            # Remove empty headers
            markdown = re.sub(r'^#+\s*$', '', markdown, flags=re.MULTILINE)

            # Clean up multiple consecutive empty lines
            markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)

            # Remove leading/trailing whitespace from each line
            lines = [line.rstrip() for line in markdown.split('\n')]
            markdown = '\n'.join(lines)

            # Remove excessive whitespace at start/end
            markdown = markdown.strip()

            # Ensure consistent list formatting
            markdown = re.sub(r'^[\*\-\+]\s+', '- ', markdown, flags=re.MULTILINE)

            # Clean up header spacing
            markdown = re.sub(r'^(#{1,6})\s*(.+)$', r'\1 \2', markdown, flags=re.MULTILINE)

            return markdown

        except Exception as e:
            raise ContentProcessingError(
                f"Error cleaning markdown: {str(e)}",
                processing_stage="markdown_cleaning"
            )

    def extract_text_summary(self, content: str, max_length: int = 200) -> str:
        """Extract a text summary from content.

        Args:
            content: Content to summarize
            max_length: Maximum summary length

        Returns:
            Summary text
        """
        try:
            # Remove markdown formatting for summary
            text = re.sub(r'[#*_`\[\]()]', '', content)
            text = re.sub(r'\n+', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            # Truncate to max length
            if len(text) <= max_length:
                return text

            # Find a good breaking point (end of sentence or word)
            truncated = text[:max_length]

            # Try to break at sentence end
            last_period = truncated.rfind('.')
            last_exclamation = truncated.rfind('!')
            last_question = truncated.rfind('?')

            sentence_end = max(last_period, last_exclamation, last_question)

            if sentence_end > max_length * 0.7:  # If sentence break is reasonably close
                return truncated[:sentence_end + 1]

            # Otherwise break at word boundary
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.8:
                return truncated[:last_space] + '...'

            return truncated + '...'

        except Exception as e:
            logger.warning(f"Error extracting summary: {str(e)}")
            return content[:max_length] + '...' if len(content) > max_length else content

    def get_content_stats(self, content: str) -> Dict[str, int]:
        """Get statistics about the content.

        Args:
            content: Content to analyze

        Returns:
            Dictionary with content statistics
        """
        try:
            # Basic stats
            char_count = len(content)
            word_count = len(content.split())
            line_count = len(content.split('\n'))

            # Markdown-specific stats
            header_count = len(re.findall(r'^#+', content, flags=re.MULTILINE))
            link_count = len(re.findall(r'\[.*?\]\(.*?\)', content))
            code_block_count = len(re.findall(r'```', content)) // 2

            return {
                'characters': char_count,
                'words': word_count,
                'lines': line_count,
                'headers': header_count,
                'links': link_count,
                'code_blocks': code_block_count
            }

        except Exception as e:
            logger.warning(f"Error calculating content stats: {str(e)}")
            return {
                'characters': len(content),
                'words': len(content.split()),
                'lines': len(content.split('\n')),
                'headers': 0,
                'links': 0,
                'code_blocks': 0
            }
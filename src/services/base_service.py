"""
Base service class that provides common functionality for all services
"""
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

# Use absolute imports for better compatibility
from src.config import get_config
from src.utils.webdriver_pool import get_webdriver_pool
from src.utils.rate_limiter import get_rate_limiter
from src.utils.file_manager import FileManager

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common functionality."""

    def __init__(self):
        """Initialize the base service."""
        self.config = get_config()
        self.webdriver_pool = get_webdriver_pool()
        self.rate_limiter = get_rate_limiter()
        self.file_manager = FileManager()

    def get_timestamp(self, format_str: str = '%Y%m%d') -> str:
        """
        Get current timestamp in the specified format.

        Args:
            format_str: Format string for the timestamp

        Returns:
            str: Formatted timestamp
        """
        return datetime.now().strftime(format_str)

    def save_data_with_retry(self, data: Dict[str, Any], filename: str, category: str, max_retries: int = 3) -> bool:
        """
        Save data with retry logic.

        Args:
            data: Data to save
            filename: Name of the file
            category: Category of data
            max_retries: Maximum number of retries

        Returns:
            bool: True if save was successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                result = self.file_manager.save_data(data, filename, category)
                if result:
                    return True
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Retrying save attempt {attempt + 1} of {max_retries}")
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Save attempt {attempt + 1} failed: {str(e)}. Retrying...")
                else:
                    logger.error(f"All save attempts failed for {filename}")
        return False

    def load_data(self, filename: str, category: str) -> Optional[Dict[str, Any]]:
        """
        Load data from a file.

        Args:
            filename: Name of the file
            category: Category of data

        Returns:
            dict: Loaded data or None if loading failed
        """
        try:
            return self.file_manager.load_data(filename, category)
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {str(e)}")
            return None

    def get_page_with_rate_limit(self, url: str, domain: str = "default") -> Optional[str]:
        """
        Get a web page with rate limiting.

        Args:
            url: URL to fetch
            domain: Domain for rate limiting

        Returns:
            str: Page content or None if fetching failed
        """
        # Wait if needed to respect rate limits
        self.rate_limiter.wait_if_needed(domain)

        # Get a WebDriver from the pool
        driver = self.webdriver_pool.get_driver()
        if not driver:
            logger.error("Could not get WebDriver from pool")
            return None

        try:
            # Navigate to the URL
            logger.info(f"Navigating to {url}")
            driver.get(url)

            # Record the request for rate limiting
            self.rate_limiter.record_request(domain)

            # Get the page source
            page_source = driver.page_source
            return page_source

        except Exception as e:
            logger.error(f"Error fetching page {url}: {str(e)}")
            return None

        finally:
            # Release the WebDriver back to the pool
            self.webdriver_pool.release_driver(driver)

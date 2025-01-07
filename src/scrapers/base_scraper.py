from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from datetime import datetime
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from utils import get_logger, FileManager

logger = get_logger('scraper.base')

class BaseScraper:
    def __init__(self):
        """Initialize the base scraper with Selenium WebDriver"""
        self.driver = None
        self.file_manager = FileManager()
        self.screenshot_dir = os.path.join(self.file_manager.get_debug_dir(), 'screenshots')
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.setup_driver()
    
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        try:
            logger.info("Setting up Chrome WebDriver...")
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920x1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--start-maximized')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-popup-blocking')
            
            # Let Selenium Manager handle driver installation
            self.driver = webdriver.Chrome(options=options)
            logger.info("Successfully initialized Chrome WebDriver")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            self.take_screenshot("driver_init_error")
            raise
    
    def get_page(self, url, timeout=10):
        """
        Get a page using Selenium with proper error handling
        
        Args:
            url (str): The URL to fetch
            timeout (int): Maximum time to wait for page load in seconds
            
        Returns:
            bool: True if page was loaded successfully, False otherwise
        """
        try:
            self.driver.get(url)
            # Wait for body to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.debug(f"Successfully loaded page: {url}")
            return True
        except TimeoutException:
            logger.error(f"Timeout waiting for page to load: {url}")
            self.take_screenshot("page_load_timeout")
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver error accessing {url}: {e}")
            self.take_screenshot("webdriver_error")
            return False
        except Exception as e:
            logger.error(f"Unexpected error accessing {url}: {e}")
            self.take_screenshot("unexpected_error")
            return False
    
    def wait_for_element(self, by, value, timeout=10, take_screenshot=True):
        """
        Wait for an element to be present on the page
        
        Args:
            by: By.ID, By.CSS_SELECTOR, etc.
            value: The selector value
            timeout: Maximum time to wait in seconds
            take_screenshot: Whether to take a screenshot on failure
            
        Returns:
            The element if found, None otherwise
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            logger.debug(f"Found element: {value}")
            return element
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {value}")
            if take_screenshot:
                self.take_screenshot(f"element_not_found_{value}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for element {value}: {e}")
            if take_screenshot:
                self.take_screenshot(f"element_error_{value}")
            return None
    
    def take_screenshot(self, reason):
        """
        Take a screenshot of the current page state
        
        Args:
            reason: The reason for taking the screenshot (used in filename)
        """
        if not self.driver:
            logger.error("Cannot take screenshot - driver not initialized")
            return
            
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{reason}_{timestamp}.png"
            filepath = os.path.join(self.screenshot_dir, filename)
            
            # Ensure the entire page is captured
            total_height = self.driver.execute_script("return document.body.parentNode.scrollHeight")
            self.driver.set_window_size(1920, total_height)
            
            self.driver.save_screenshot(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            
            # Reset window size
            self.driver.set_window_size(1920, 1080)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
    
    def get_page_source(self):
        """Get the current page source with error handling"""
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Failed to get page source: {e}")
            self.take_screenshot("page_source_error")
            return None
    
    def scroll_to_element(self, element):
        """Scroll element into view with error handling"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            # Wait a bit for any dynamic content to load
            self.driver.implicitly_wait(1)
        except Exception as e:
            logger.error(f"Failed to scroll to element: {e}")
            self.take_screenshot("scroll_error")
    
    def __del__(self):
        """Clean up WebDriver when object is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
                self.take_screenshot("driver_cleanup_error")

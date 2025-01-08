import os
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from utils import get_logger
from debug.html_analyzer import HTMLAnalyzer

logger = get_logger()

class BaseScraper:
    def __init__(self):
        """Initialize the base scraper with WebDriver setup"""
        self.driver = None
        self.html_analyzer = HTMLAnalyzer()
        self.setup_driver()
        
    def setup_driver(self, max_retries: int = 3):
        """
        Set up Chrome WebDriver with retries
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        logger.info("Setting up Chrome WebDriver...")
        
        for attempt in range(max_retries):
            try:
                if self.driver is not None:
                    self.cleanup()
                
                options = Options()
                # options.add_argument('--headless')  # Run in headless mode
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                
                try:
                    # Create a new Service instance
                    service = Service()
                    
                    # Create the WebDriver instance
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self.driver.set_page_load_timeout(30)  # Set page load timeout
                    
                    logger.info("Successfully initialized Chrome WebDriver")
                    return
                except WebDriverException as e:
                    if "chromedriver" in str(e).lower():
                        logger.error("ChromeDriver not found. Please install it using: brew install chromedriver")
                    raise
                
            except WebDriverException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"WebDriver setup attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(1)  # Wait before retrying
                else:
                    logger.error("Failed to set up WebDriver after all attempts")
                    raise
    
    def get_page(self, url: str, max_retries: int = 3) -> bool:
        """
        Load a webpage with retry logic
        
        Args:
            url: URL to load
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if page loaded successfully, False otherwise
        """
        for attempt in range(max_retries):
            try:
                if self.driver is None:
                    self.setup_driver()
                
                self.driver.get(url)
                time.sleep(2)  # Wait for page to load
                
                # Analyze the page for debugging
                self.html_analyzer.analyze_page(url, self.driver)
                
                return True
                
            except WebDriverException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Page load attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    self.setup_driver()  # Reinitialize driver
                    time.sleep(1)  # Wait before retrying
                else:
                    logger.error(f"Failed to load page {url} after all attempts")
                    return False
                    
        return False
    
    def cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error during WebDriver cleanup: {str(e)}")
            finally:
                self.driver = None
    
    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.cleanup()

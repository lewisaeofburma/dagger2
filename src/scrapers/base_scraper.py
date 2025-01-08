import os
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium_stealth import stealth
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
                
                options = webdriver.ChromeOptions()
                # options.add_argument("--headless")  # Commented for debugging
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--start-maximized")
                options.add_argument("--disable-notifications")
                options.add_argument("--disable-popup-blocking")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                
                # Add user agent for better stealth
                options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
                
                try:
                    self.driver = webdriver.Chrome(options=options)
                    
                    # Apply stealth settings
                    stealth(self.driver,
                           languages=["en-US", "en"],
                           vendor="Google Inc.",
                           platform="Win32",
                           webgl_vendor="Intel Inc.",
                           renderer="Intel Iris OpenGL Engine",
                           fix_hairline=True)
                    
                    self.driver.set_page_load_timeout(30)
                    logger.info("Successfully initialized Chrome WebDriver with stealth mode")
                    return
                    
                except WebDriverException as e:
                    if "chromedriver" in str(e).lower():
                        logger.error("ChromeDriver not found. Please install Chrome browser and ChromeDriver")
                    raise
                
            except WebDriverException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"WebDriver setup attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(1)
                else:
                    logger.error("Failed to set up WebDriver after all attempts")
                    raise
    
    def get_page(self, url: str, max_retries: int = 3) -> bool:
        """
        Navigate to a URL with retry logic
        
        Args:
            url: URL to navigate to
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Navigating to {url}")
        
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                return True
            except WebDriverException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Page load attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to load page after {max_retries} attempts: {str(e)}")
                    return False
        return False
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error during cleanup: {str(e)}")
            finally:
                self.driver = None
    
    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.cleanup()

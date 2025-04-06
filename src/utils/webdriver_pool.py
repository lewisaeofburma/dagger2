"""
WebDriver pool implementation to efficiently manage and reuse WebDriver instances
"""
import time
import queue
import threading
import logging
from typing import Optional, List, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium_stealth import stealth

from src.config import get_config

logger = logging.getLogger(__name__)


class WebDriverPool:
    """
    A pool of WebDriver instances that can be reused.
    Implements the Singleton pattern to ensure only one pool exists.
    """
    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        """Implement singleton pattern with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WebDriverPool, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the WebDriver pool."""
        with self._lock:
            if self._initialized:
                return

            self.config = get_config()
            self.pool = queue.Queue()
            self.active_drivers = set()
            self.max_size = self.config.get('webdriver_pool_size', 3)
            self.current_size = 0
            self._initialized = True
            logger.info(
                f"WebDriver pool initialized with max size: {self.max_size}")

    def get_driver(self, wait_timeout: int = 30) -> Optional[webdriver.Chrome]:
        """
        Get a WebDriver instance from the pool or create a new one if needed.

        Args:
            wait_timeout: Maximum time to wait for an available driver

        Returns:
            WebDriver instance or None if none available
        """
        with self._lock:
            try:
                # Try to get a driver from the pool
                driver = self.pool.get(block=True, timeout=wait_timeout)
                logger.debug("Retrieved WebDriver from pool")
                self.active_drivers.add(driver)
                return driver
            except queue.Empty:
                # If pool is empty, create a new driver if below max size
                if self.current_size < self.max_size:
                    driver = self._create_driver()
                    if driver:
                        self.current_size += 1
                        self.active_drivers.add(driver)
                        logger.debug(
                            f"Created new WebDriver, pool size: {self.current_size}")
                        return driver

                logger.warning(
                    "Could not get WebDriver: pool exhausted and at max size")
                return None

    def release_driver(self, driver: webdriver.Chrome) -> None:
        """
        Release a WebDriver back to the pool.

        Args:
            driver: WebDriver instance to release
        """
        with self._lock:
            if driver in self.active_drivers:
                try:
                    # Clear cookies and reset state before returning to pool
                    driver.delete_all_cookies()
                    driver.get("about:blank")

                    self.active_drivers.remove(driver)
                    self.pool.put(driver)
                    logger.debug("Released WebDriver back to pool")
                except Exception as e:
                    logger.error(f"Error releasing WebDriver: {str(e)}")
                    self._close_driver(driver)
            else:
                logger.warning("Attempted to release untracked WebDriver")

    def _create_driver(self) -> Optional[webdriver.Chrome]:
        """
        Create a new WebDriver instance.

        Returns:
            New WebDriver instance or None if creation failed
        """
        try:
            settings = self.config.get('webdriver_settings', {})

            options = webdriver.ChromeOptions()

            if settings.get('headless', False):
                options.add_argument("--headless")

            if settings.get('no_sandbox', True):
                options.add_argument("--no-sandbox")

            if settings.get('disable_dev_shm_usage', True):
                options.add_argument("--disable-dev-shm-usage")

            if settings.get('disable_blink_features', None):
                options.add_argument(
                    f"--disable-blink-features={settings['disable_blink_features']}")

            if settings.get('start_maximized', True):
                options.add_argument("--start-maximized")

            if settings.get('disable_notifications', True):
                options.add_argument("--disable-notifications")

            if settings.get('disable_popup_blocking', True):
                options.add_argument("--disable-popup-blocking")

            options.add_experimental_option(
                "excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # Add user agent
            user_agent = settings.get('user_agent', '')
            if user_agent:
                options.add_argument(f"user-agent={user_agent}")

            # Create the WebDriver
            driver = webdriver.Chrome(options=options)

            # Apply stealth settings
            stealth_settings = settings.get('stealth_settings', {})
            if stealth_settings:
                stealth(
                    driver,
                    languages=stealth_settings.get(
                        'languages', ["en-US", "en"]),
                    vendor=stealth_settings.get('vendor', "Google Inc."),
                    platform=stealth_settings.get('platform', "Win32"),
                    webgl_vendor=stealth_settings.get(
                        'webgl_vendor', "Intel Inc."),
                    renderer=stealth_settings.get(
                        'renderer', "Intel Iris OpenGL Engine"),
                    fix_hairline=stealth_settings.get('fix_hairline', True)
                )

            # Set page load timeout
            timeout = self.config.get('page_load_timeout', 30)
            driver.set_page_load_timeout(timeout)

            return driver

        except WebDriverException as e:
            logger.error(f"Error creating WebDriver: {str(e)}")
            return None

    def _close_driver(self, driver: webdriver.Chrome) -> None:
        """
        Close a WebDriver instance and update pool size.

        Args:
            driver: WebDriver instance to close
        """
        with self._lock:
            try:
                if driver in self.active_drivers:
                    self.active_drivers.remove(driver)

                driver.quit()
                self.current_size -= 1
                logger.debug(
                    f"Closed WebDriver, pool size: {self.current_size}")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
                # Ensure we decrement the count even if there's an error
                self.current_size = max(0, self.current_size - 1)

    def close_all(self) -> None:
        """Close all WebDriver instances in the pool."""
        with self._lock:
            # Close active drivers
            active_drivers = list(self.active_drivers)
            for driver in active_drivers:
                self._close_driver(driver)

            # Close drivers in the pool
            while not self.pool.empty():
                try:
                    driver = self.pool.get(block=False)
                    driver.quit()
                    self.current_size -= 1
                except Exception as e:
                    logger.error(f"Error closing pooled WebDriver: {str(e)}")

            self.current_size = 0
            logger.info("Closed all WebDrivers in pool")


# Create a singleton instance
_pool = WebDriverPool()


def get_webdriver_pool() -> WebDriverPool:
    """
    Get the WebDriver pool instance.

    Returns:
        WebDriverPool: The WebDriver pool instance
    """
    return _pool

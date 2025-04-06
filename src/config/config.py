"""
Configuration module for the football analysis application.
Centralizes all configuration settings and provides a consistent interface.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

# Base directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = PROJECT_ROOT / 'src'
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
DEBUG_DIR = PROJECT_ROOT / 'debug'

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, DEBUG_DIR]:
    directory.mkdir(exist_ok=True)

# Data subdirectories
TEAMS_DIR = DATA_DIR / 'teams'
STANDINGS_DIR = DATA_DIR / 'standings'
PROCESSED_DIR = DATA_DIR / 'processed'
VISUALIZATIONS_DIR = DATA_DIR / 'visualizations'

# Create data subdirectories
for directory in [TEAMS_DIR, STANDINGS_DIR, PROCESSED_DIR, VISUALIZATIONS_DIR]:
    directory.mkdir(exist_ok=True)

# URLs
FBREF_BASE_URL = "https://fbref.com"
PREMIER_LEAGUE_URL = f"{FBREF_BASE_URL}/en/comps/9/Premier-League-Stats"

# Scraping settings
RETRY_COUNT = 3
PAGE_LOAD_TIMEOUT = 30
REQUEST_TIMEOUT = 30
EXPONENTIAL_BACKOFF_BASE = 2

# Rate limiting settings
RATE_LIMIT_REQUESTS = 10  # Number of requests
RATE_LIMIT_PERIOD = 60    # Time period in seconds

# WebDriver settings
WEBDRIVER_SETTINGS = {
    'headless': False,  # Set to True for production
    'no_sandbox': True,
    'disable_dev_shm_usage': True,
    'disable_blink_features': 'AutomationControlled',
    'start_maximized': True,
    'disable_notifications': True,
    'disable_popup_blocking': True,
    'window_size': (1920, 1080),
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'stealth_settings': {
        'languages': ["en-US", "en"],
        'vendor': "Google Inc.",
        'platform': "MacOS",  # Match with user agent
        'webgl_vendor': "Intel Inc.",
        'renderer': "Intel Iris OpenGL Engine",
        'fix_hairline': True
    }
}

# Logging settings
LOGGING_CONFIG = {
    'console_level': logging.INFO,
    'file_level': logging.DEBUG,
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'console_format': '%(levelname)s: %(message)s',
    'max_file_size': 5 * 1024 * 1024,  # 5MB
    'backup_count': 5
}

# Teams to analyze (empty list means all teams)
TEAMS_TO_ANALYZE = []  # Empty list means all teams

# File retention settings
FILE_RETENTION_DAYS = 30  # Number of days to keep files before cleanup

class Config:
    """Configuration class that provides access to all settings."""
    
    _instance = None
    _config_file = PROJECT_ROOT / 'config.json'
    _config_data = {}
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration."""
        if self._initialized:
            return
            
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """Load configuration from file if it exists."""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r') as f:
                    self._config_data = json.load(f)
                    logging.info(f"Loaded configuration from {self._config_file}")
            except Exception as e:
                logging.error(f"Error loading configuration: {str(e)}")
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self._config_file, 'w') as f:
                json.dump(self._config_data, f, indent=2)
                logging.info(f"Saved configuration to {self._config_file}")
        except Exception as e:
            logging.error(f"Error saving configuration: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key is not found
            
        Returns:
            The configuration value
        """
        # First check in the loaded config
        if key in self._config_data:
            return self._config_data[key]
            
        # Then check in module constants
        if key.upper() in globals():
            return globals()[key.upper()]
            
        return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The value to set
        """
        self._config_data[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary with all configuration values
        """
        config = {}
        
        # Add all module constants
        for key in globals():
            if key.isupper() and not key.startswith('_'):
                config[key.lower()] = globals()[key]
                
        # Override with loaded config
        for key, value in self._config_data.items():
            config[key] = value
            
        return config

# Create a singleton instance
config = Config()

def get_config() -> Config:
    """
    Get the configuration instance.
    
    Returns:
        Config: The configuration instance
    """
    return config
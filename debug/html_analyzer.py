import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from selenium.webdriver.remote.webdriver import WebDriver

# Set up logging
def setup_logging():
    """Set up logging configuration"""
    log_dir = Path(__file__).resolve().parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'html_analyzer_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class HTMLAnalyzer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HTMLAnalyzer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the HTML Analyzer (singleton)"""
        if self._initialized:
            return
            
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.output_dir = Path(__file__).resolve().parent / 'output'
        self.output_dir.mkdir(exist_ok=True)
        
        self.screenshot_dir = self.output_dir / 'screenshots'
        self.screenshot_dir.mkdir(exist_ok=True)
        
        logger.info("HTML Analyzer initialized")
        self._initialized = True

    def analyze_page(self, url: str, driver: Optional[WebDriver] = None, save_html: bool = False) -> Optional[str]:
        """
        Analyze a webpage and save relevant information for debugging
        
        Args:
            url: URL to analyze
            driver: Optional WebDriver instance for dynamic content
            save_html: Whether to save the raw HTML content
            
        Returns:
            str: Path to the debug file
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_file = self.output_dir / f'page_analysis_{timestamp}.txt'
            
            logger.info(f"Analyzing page: {url}")
            
            # Get page content
            if driver:
                page_source = driver.page_source
            else:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                page_source = response.text
            
            # Save raw HTML if requested
            if save_html:
                html_file = self.output_dir / f'raw_html_{timestamp}.html'
                html_file.write_text(page_source, encoding='utf-8')
                logger.info(f"Raw HTML saved to: {html_file}")

            soup = BeautifulSoup(page_source, 'html.parser')
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                # Basic Information
                f.write(f"=== PAGE ANALYSIS ===\n")
                f.write(f"URL: {url}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Content Type: {response.headers.get('content-type', 'N/A') if not driver else 'From WebDriver'}\n\n")

                # Page Title and Meta
                f.write("=== PAGE METADATA ===\n")
                title = soup.find('title')
                f.write(f"Title: {title.text if title else 'No title found'}\n")
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                f.write(f"Description: {meta_desc['content'] if meta_desc else 'No description found'}\n\n")

                # Table Analysis
                f.write("=== TABLE ANALYSIS ===\n")
                tables = soup.find_all('table')
                for idx, table in enumerate(tables, 1):
                    f.write(f"\nTable #{idx}\n")
                    f.write(f"ID: {table.get('id', 'No ID')}\n")
                    f.write(f"Class: {' '.join(table.get('class', []))}\n")
                    
                    # Analyze headers
                    headers = table.find_all('th')
                    if headers:
                        f.write("Headers:\n")
                        for header in headers:
                            data_stat = header.get('data-stat', 'No data-stat')
                            text = header.text.strip()
                            f.write(f"  - {text} (data-stat: {data_stat})\n")
                    
                    # Sample first row data
                    first_row = table.find('tr', class_=lambda x: x != 'thead')
                    if first_row:
                        f.write("Sample Row Data:\n")
                        cells = first_row.find_all(['td', 'th'])
                        for cell in cells:
                            data_stat = cell.get('data-stat', 'No data-stat')
                            text = cell.text.strip()
                            f.write(f"  - {data_stat}: {text}\n")
                    f.write("\n")

                # Data Attributes Analysis
                f.write("=== DATA ATTRIBUTES ANALYSIS ===\n")
                elements_with_data = soup.find_all(attrs={'data-stat': True})
                data_stats = {}
                for elem in elements_with_data:
                    stat = elem.get('data-stat')
                    if stat not in data_stats:
                        data_stats[stat] = {
                            'count': 0,
                            'sample': elem.text.strip()[:50]
                        }
                    data_stats[stat]['count'] += 1

                for stat, info in sorted(data_stats.items()):
                    f.write(f"data-stat: {stat}\n")
                    f.write(f"  Count: {info['count']}\n")
                    f.write(f"  Sample: {info['sample']}\n")

            logger.info(f"Analysis completed and saved to: {debug_file}")
            return debug_file

        except Exception as e:
            logger.error(f"Error analyzing page: {str(e)}", exc_info=True)
            return None

    def take_screenshot(self, driver: WebDriver, reason: str) -> Optional[str]:
        """
        Take a screenshot of the current page state
        
        Args:
            driver: WebDriver instance
            reason: Reason for taking the screenshot (used in filename)
            
        Returns:
            str: Path to the screenshot file
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{reason}_{timestamp}.png"
            filepath = self.screenshot_dir / filename
            
            # Ensure the entire page is captured
            total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
            driver.set_window_size(1920, total_height)
            
            driver.save_screenshot(str(filepath))
            logger.info(f"Screenshot saved: {filepath}")
            
            # Reset window size
            driver.set_window_size(1920, 1080)
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}", exc_info=True)
            return None

    def cleanup_files(self, max_files: int = 5) -> None:
        """
        Clean up debug files, keeping only the specified number of most recent files
        
        Args:
            max_files: Maximum number of files to keep
        """
        try:
            # Get all analysis and HTML files
            analysis_files = list(self.output_dir.glob('page_analysis_*.txt'))
            html_files = list(self.output_dir.glob('raw_html_*.html'))
            screenshot_files = list(self.screenshot_dir.glob('*.png'))
            
            # Sort files by modification time
            for files in [analysis_files, html_files, screenshot_files]:
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remove old files
                for file in files[max_files:]:
                    file.unlink()
                    logger.debug(f"Removed old debug file: {file}")

            logger.info(f"Cleanup completed. Keeping {max_files} most recent files of each type.")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)

if __name__ == "__main__":
    analyzer = HTMLAnalyzer()
    
    # Test with Liverpool's page
    url = "https://fbref.com/en/squads/822bd0ba/Liverpool-Stats"
    debug_file = analyzer.analyze_page(url, save_html=True)
    
    if debug_file:
        print(f"Analysis saved to: {debug_file}")
        analyzer.cleanup_files()

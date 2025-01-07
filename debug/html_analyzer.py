import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils import setup_logging, create_data_directory

logger = setup_logging()

class HTMLAnalyzer:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.debug_dir = self._create_debug_directory()

    def _create_debug_directory(self):
        """Create debug directory if it doesn't exist"""
        debug_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug')
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir)
        return debug_dir

    def analyze_page(self, url):
        """Analyze a webpage and save relevant information for debugging"""
        try:
            # Generate timestamp for the debug file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_file = os.path.join(self.debug_dir, f'page_analysis_{timestamp}.txt')

            # Fetch the page
            logger.info(f"Fetching page for analysis: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Open debug file for writing
            with open(debug_file, 'w', encoding='utf-8') as f:
                # Write URL and timestamp
                f.write(f"URL: {url}\n")
                f.write(f"Timestamp: {timestamp}\n\n")

                # Find all tables and their IDs
                f.write("=== TABLE IDs ===\n")
                tables = soup.find_all('table')
                for table in tables:
                    table_id = table.get('id', 'No ID')
                    f.write(f"Table ID: {table_id}\n")
                    
                    # Get header information
                    headers = table.find_all('th')
                    if headers:
                        f.write("Data attributes in headers:\n")
                        for header in headers:
                            data_stat = header.get('data-stat', 'No data-stat')
                            f.write(f"  - {data_stat}\n")
                    f.write("\n")

                # Find all elements with data-stat attributes
                f.write("=== ALL DATA-STAT ATTRIBUTES ===\n")
                elements_with_data_stat = soup.find_all(attrs={'data-stat': True})
                unique_data_stats = set(elem.get('data-stat') for elem in elements_with_data_stat)
                for data_stat in sorted(unique_data_stats):
                    f.write(f"data-stat: {data_stat}\n")

            logger.info(f"Page analysis saved to: {debug_file}")
            return debug_file

        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
            return None

    def cleanup_debug_files(self, keep_latest=False):
        """Clean up debug files, optionally keeping the latest one"""
        try:
            files = [f for f in os.listdir(self.debug_dir) if f.startswith('page_analysis_')]
            if not files:
                return

            # Sort files by timestamp (newest first)
            files.sort(reverse=True)

            # Keep the latest 5 files for debugging purposes
            files_to_remove = files[5:] if keep_latest else files[1:]

            # Remove old files
            for file in files_to_remove:
                file_path = os.path.join(self.debug_dir, file)
                os.remove(file_path)
                logger.debug(f"Removed debug file: {file}")

        except Exception as e:
            logger.error(f"Error cleaning up debug files: {e}")

if __name__ == "__main__":
    analyzer = HTMLAnalyzer()
    url = "https://fbref.com/en/comps/9/Premier-League-Stats"
    debug_file = analyzer.analyze_page(url)
    if debug_file:
        print(f"Analysis saved to: {debug_file}")

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from scrapers.base_scraper import BaseScraper
from utils import get_logger

logger = get_logger('scraper.teams')

class FBRefScraper(BaseScraper):
    def __init__(self):
        """Initialize the FBRef scraper"""
        super().__init__()
        self.base_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
        self.debug_dir = os.path.join(str(Path(__file__).resolve().parent.parent.parent), 'debug')
        os.makedirs(self.debug_dir, exist_ok=True)
        
    def analyze_page_structure(self):
        """Analyze the page structure and save it for debugging"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_file = os.path.join(self.debug_dir, f'page_analysis_{timestamp}.txt')
            
            # Get page source and parse with BeautifulSoup
            page_source = self.get_page_source()
            if not page_source:
                return None
                
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Save analysis to file
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {self.base_url}\n")
                f.write(f"Timestamp: {timestamp}\n\n")
                
                # Find all tables
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
                
            logger.info(f"Page analysis saved to: {debug_file}")
            return debug_file
            
        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
            return None
        
    def get_premier_league_teams(self):
        """
        Fetch Premier League teams from FBRef
        
        Returns:
            list: List of dictionaries containing team information
        """
        logger.info("Fetching Premier League teams...")
        logger.info(f"Fetching Premier League teams from: {self.base_url}")
        
        if not self.get_page(self.base_url):
            logger.error("Failed to load Premier League stats page")
            return None
            
        try:
            # First analyze the page structure
            debug_file = self.analyze_page_structure()
            if debug_file:
                logger.info(f"Page structure analysis saved to: {debug_file}")
            
            teams = []
            # Try to find the standings table
            table = self.wait_for_element(By.CSS_SELECTOR, "table#results2024-202591_overall")
            
            if not table:
                logger.error("Could not find teams table")
                return None
                
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr:not(.spacer):not(.thead)")
            
            for row in rows:
                try:
                    # Try different selectors for team name
                    team_cell = row.find_element(By.CSS_SELECTOR, "td[data-stat='team'] a")
                    
                    team_name = team_cell.text.strip()
                    team_url = team_cell.get_attribute("href")
                    
                    if team_name and team_url:
                        teams.append({
                            "name": team_name,
                            "url": team_url
                        })
                        logger.info(f"Found team: {team_name}")
                except NoSuchElementException:
                    logger.warning("Skipping row with missing team data")
                    continue
                except Exception as e:
                    logger.error(f"Error processing team row: {e}")
                    continue
            
            if not teams:
                logger.error("No teams were found")
            else:
                logger.info(f"Successfully found {len(teams)} teams")
                
            return teams
            
        except Exception as e:
            logger.error(f"Error fetching Premier League teams: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    scraper = FBRefScraper()
    teams = scraper.get_premier_league_teams()
    if teams is not None:
        logger.info("\nPremier League Teams:")
        for team in teams:
            logger.info(f"- {team['name']}")

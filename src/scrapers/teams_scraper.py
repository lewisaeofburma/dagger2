from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

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
        
    def get_premier_league_teams(self) -> Optional[List[Dict[str, str]]]:
        """
        Fetch Premier League teams from FBRef
        
        Returns:
            list: List of dictionaries containing team information
        """
        logger.info(f"Fetching Premier League teams from: {self.base_url}")
        
        try:
            if not self.get_page(self.base_url):
                logger.error("Failed to load Premier League stats page")
                return None
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the table containing team data
            teams_table = soup.find('table', {'id': 'results2024-202591_overall'})
            if not teams_table:
                logger.error("Could not find teams table")
                return None
            
            teams = []
            team_rows = teams_table.find('tbody')
            if not team_rows:
                logger.error("Could not find table body")
                return None
            
            team_rows = team_rows.find_all('tr')
            
            for row in team_rows:
                team_cell = row.find('td', {'data-stat': 'team'})
                if team_cell:
                    team_link = team_cell.find('a')
                    if team_link:
                        team_name = team_link.text.strip()
                        team_url = f"https://fbref.com{team_link['href']}"
                        teams.append({
                            'name': team_name,
                            'url': team_url
                        })
                        logger.info(f"Found team: {team_name}")
            
            if teams:
                logger.info(f"Successfully found {len(teams)} teams")
                return teams
            else:
                logger.error("No teams found in the table")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Premier League teams: {str(e)}")
            return None
        finally:
            self.cleanup()

if __name__ == "__main__":
    scraper = FBRefScraper()
    teams = scraper.get_premier_league_teams()
    if teams is not None:
        logger.info("\nPremier League Teams:")
        for team in teams:
            logger.info(f"- {team['name']}")

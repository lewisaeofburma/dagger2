from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from bs4 import BeautifulSoup

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from scrapers.base_scraper import BaseScraper
from utils import get_logger

logger = get_logger('scraper.league_stats')

class LeagueStatsScraper(BaseScraper):
    def __init__(self):
        """Initialize the League Stats scraper"""
        super().__init__()
        self.base_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
        
    def get_league_standings(self) -> Optional[List[Dict[str, str]]]:
        """
        Get Premier League standings
        
        Returns:
            list: List of dictionaries containing team standings, or None if error occurs
        """
        logger.info("Fetching Premier League standings...")
        
        try:
            if not self.get_page(self.base_url):
                logger.error("Failed to load Premier League standings page")
                return None
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the standings table
            standings_table = soup.find('table', {'id': 'results2024-202591_overall'})
            if not standings_table:
                logger.error("Could not find standings table")
                return None
            
            standings = []
            team_rows = standings_table.find('tbody').find_all('tr')
            
            for row in team_rows:
                team_data = {}
                
                # Get all cells in the row
                for cell in row.find_all(['td', 'th']):
                    stat_name = cell.get('data-stat')
                    if stat_name:
                        team_data[stat_name] = cell.text.strip()
                
                if team_data:
                    # Add rank if not present
                    if 'rank' not in team_data and len(standings) + 1 <= 20:
                        team_data['rank'] = str(len(standings) + 1)
                    
                    # Clean up stats
                    team_data['team'] = team_data.get('team', 'Unknown')
                    team_data['points'] = team_data.get('points', '0')
                    team_data['wins'] = team_data.get('wins', '0')
                    team_data['draws'] = team_data.get('ties', '0')  # FBRef uses 'ties' for draws
                    team_data['losses'] = team_data.get('losses', '0')
                    team_data['goals_for'] = team_data.get('goals_for', '0')
                    team_data['goals_against'] = team_data.get('goals_against', '0')
                    team_data['goal_diff'] = team_data.get('goal_diff', '0')
                    
                    standings.append(team_data)
                    logger.info(f"Found team: {team_data['team']} - {team_data['points']} pts")
            
            if standings:
                logger.info(f"Successfully found {len(standings)} teams in standings")
                return standings
            else:
                logger.error("No teams found in standings")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching league standings: {str(e)}")
            return None
        
    def get_team_stats(self) -> Optional[List[Dict[str, Union[str, float, int]]]]:
        """
        Get team statistics
        
        Returns:
            list: List of dictionaries containing team statistics
        """
        logger.info("Fetching team statistics...")
        
        try:
            if not self.get_page(self.base_url):
                logger.error("Failed to load team statistics page")
                return None
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the statistics table
            stats_table = soup.find('table', {'id': 'stats_squads_standard_for'})
            if not stats_table:
                logger.error("Could not find statistics table")
                return None
            
            stats = []
            team_rows = stats_table.find('tbody').find_all('tr')
            
            for row in team_rows:
                team_data = {}
                
                # Get all cells in the row
                for cell in row.find_all(['td', 'th']):
                    stat_name = cell.get('data-stat')
                    if stat_name:
                        team_data[stat_name] = cell.text.strip()
                
                if team_data:
                    # Clean up stats
                    team_data['team'] = team_data.get('team', 'Unknown')
                    team_data['possession'] = team_data.get('possession', '0')
                    team_data['goals'] = team_data.get('goals', '0')
                    team_data['assists'] = team_data.get('assists', '0')
                    team_data['xg'] = team_data.get('xg', '0')
                    team_data['xg_assist'] = team_data.get('xg_assist', '0')
                    
                    # Convert stats to float or int if possible
                    for stat, value in team_data.items():
                        if stat != 'team':
                            try:
                                team_data[stat] = float(value) if '.' in value else int(value)
                            except ValueError:
                                pass
                    
                    stats.append(team_data)
                    logger.info(f"Found team statistics for {team_data['team']}")
            
            if stats:
                logger.info(f"Successfully found statistics for {len(stats)} teams")
                return stats
            else:
                logger.error("No team statistics found")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching team statistics: {str(e)}")
            return None
        finally:
            self.cleanup()
            
    def __del__(self):
        """Clean up WebDriver when object is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

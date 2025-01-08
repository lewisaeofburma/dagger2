from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import sys
from pathlib import Path
import json
from datetime import datetime
import logging
from typing import Optional, Dict, List, Any, Union
from bs4 import BeautifulSoup

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Add project root to Python path for debug module
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from scrapers.base_scraper import BaseScraper
from utils import get_logger
from utils.file_manager import FileManager
from debug.html_analyzer import HTMLAnalyzer

logger = get_logger('scraper.team_stats')

class TeamStatsScraper(BaseScraper):
    def __init__(self):
        """Initialize the Team Stats scraper"""
        super().__init__()
        self.file_manager = FileManager()
        self.html_analyzer = HTMLAnalyzer()
        logger.info("Team Stats Scraper initialized")
        
    def _extract_table_data(self, table, exclude_cols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract data from a table
        
        Args:
            table: Selenium WebElement representing the table
            exclude_cols: List of column names to exclude
            
        Returns:
            List of dictionaries containing row data
        """
        if exclude_cols is None:
            exclude_cols = []
            
        try:
            table_id = table.get_attribute('id')
            logger.debug(f"Extracting data from table: {table_id}")
            
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr:not(.thead)")
            data = []
            
            for row_idx, row in enumerate(rows, 1):
                try:
                    row_data = {}
                    cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                    
                    for cell in cells:
                        try:
                            stat = cell.get_attribute('data-stat')
                            if stat and stat not in exclude_cols:
                                value = cell.text.strip()
                                # Convert numeric values
                                try:
                                    if '.' in value:
                                        value = float(value)
                                    elif value.isdigit():
                                        value = int(value)
                                    elif value.startswith(('+', '-')) and value[1:].isdigit():
                                        value = int(value)
                                    elif ',' in value:
                                        value = float(value.replace(',', ''))
                                except ValueError:
                                    pass
                                row_data[stat] = value
                                
                        except StaleElementReferenceException:
                            logger.warning(f"Stale element in table {table_id}, row {row_idx}")
                            continue
                            
                    if row_data:  # Only add non-empty rows
                        data.append(row_data)
                        
                except Exception as e:
                    logger.error(f"Error processing row {row_idx} in table {table_id}: {str(e)}")
                    continue
                    
            logger.debug(f"Extracted {len(data)} rows from table {table_id}")
            return data
            
        except Exception as e:
            logger.error(f"Error extracting table data: {str(e)}", exc_info=True)
            return []
            
    def get_team_stats(self, team_url: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive team statistics
        
        Args:
            team_url: URL of the team's page
            
        Returns:
            Dictionary containing team statistics
        """
        logger.info(f"Fetching team statistics from: {team_url}")
        
        try:
            # First analyze the page structure
            self.html_analyzer.analyze_page(team_url, save_html=True)
            
            if not self.get_page(team_url):
                logger.error("Failed to load team page")
                return None
                
            team_data = {
                'url': team_url,
                'timestamp': datetime.now().strftime('%Y%m%d'),
                'players': {},  # All player stats will be stored here
                'matches': []   # Keep matches separate as it's team-level data
            }
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Squad Statistics (Standard)
            squad_table = soup.find('table', {'id': 'stats_standard_9'})
            if squad_table:
                squad_rows = squad_table.find('tbody').find_all('tr')
                for row in squad_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    team_data['players'][player_name] = {
                        'url': player_url,
                        'stats': stats
                    }
                    
                    logger.debug(f"Processed player: {player_name}")
            else:
                logger.warning("Squad statistics table not found")
            
            # Match Logs
            matches_table = soup.find('table', {'id': 'matchlogs_for'})
            if matches_table:
                match_rows = matches_table.find('tbody').find_all('tr')
                for row in match_rows:
                    match_data = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            match_data[stat_name] = cell.text.strip()
                    
                    if match_data:
                        team_data['matches'].append(match_data)
            else:
                logger.warning("Match logs table not found")
            
            # Goalkeeper Statistics
            gk_table = soup.find('table', {'id': 'stats_keeper_9'})
            if gk_table:
                gk_rows = gk_table.find('tbody').find_all('tr')
                for row in gk_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['goalkeeper_stats'] = stats
            else:
                logger.warning("Goalkeeper statistics table not found")
            
            # Shooting Statistics
            shooting_table = soup.find('table', {'id': 'stats_shooting_9'})
            if shooting_table:
                shooting_rows = shooting_table.find('tbody').find_all('tr')
                for row in shooting_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['shooting_stats'] = stats
            else:
                logger.warning("Shooting statistics table not found")
            
            # Passing Statistics
            passing_table = soup.find('table', {'id': 'stats_passing_9'})
            if passing_table:
                passing_rows = passing_table.find('tbody').find_all('tr')
                for row in passing_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['passing_stats'] = stats
            else:
                logger.warning("Passing statistics table not found")
            
            # Pass Types
            pass_types_table = soup.find('table', {'id': 'stats_passing_types_9'})
            if pass_types_table:
                pass_types_rows = pass_types_table.find('tbody').find_all('tr')
                for row in pass_types_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['pass_types_stats'] = stats
            else:
                logger.warning("Pass types statistics table not found")
            
            # Goal Creation
            gca_table = soup.find('table', {'id': 'stats_gca_9'})
            if gca_table:
                gca_rows = gca_table.find('tbody').find_all('tr')
                for row in gca_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['goal_creation_stats'] = stats
            else:
                logger.warning("Goal creation statistics table not found")
            
            # Defense
            defense_table = soup.find('table', {'id': 'stats_defense_9'})
            if defense_table:
                defense_rows = defense_table.find('tbody').find_all('tr')
                for row in defense_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['defense_stats'] = stats
            else:
                logger.warning("Defense statistics table not found")
            
            # Possession
            possession_table = soup.find('table', {'id': 'stats_possession_9'})
            if possession_table:
                possession_rows = possession_table.find('tbody').find_all('tr')
                for row in possession_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['possession_stats'] = stats
            else:
                logger.warning("Possession statistics table not found")
            
            # Playing Time
            playing_time_table = soup.find('table', {'id': 'stats_playing_time_9'})
            if playing_time_table:
                playing_time_rows = playing_time_table.find('tbody').find_all('tr')
                for row in playing_time_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['playing_time_stats'] = stats
            else:
                logger.warning("Playing time statistics table not found")
            
            # Miscellaneous Stats
            misc_table = soup.find('table', {'id': 'stats_misc_9'})
            if misc_table:
                misc_rows = misc_table.find('tbody').find_all('tr')
                for row in misc_rows:
                    player_cell = row.find('th', {'data-stat': 'player'})
                    if not player_cell or not player_cell.find('a'):
                        continue
                    
                    player_name = player_cell.find('a').text.strip()
                    player_url = f"https://fbref.com{player_cell.find('a')['href']}"
                    
                    # Get all stats for the player
                    stats = {}
                    for cell in row.find_all(['td', 'th']):
                        stat_name = cell.get('data-stat')
                        if stat_name:
                            stats[stat_name] = cell.text.strip()
                    
                    if player_name in team_data['players']:
                        team_data['players'][player_name]['miscellaneous_stats'] = stats
            else:
                logger.warning("Miscellaneous statistics table not found")
            
            # After collecting all stats
            player_count = len(team_data['players'])
            logger.info(f"Successfully collected data for {player_count} players")
            
            # # Save the data
            # team_id = team_url.split('/')[-2]
            # filename = f"{team_id}_stats_{datetime.now().strftime('%Y%m%d')}.json"
            
            # try:
            #     self.file_manager.save_team_data(team_data, filename)
            #     logger.info(f"Saved team statistics to {filename}")
            # except Exception as e:
            #     logger.error(f"Error saving team data: {str(e)}", exc_info=True)
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error fetching team statistics: {str(e)}", exc_info=True)
            return None
            
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                logger.debug("Successfully closed WebDriver")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")

    def __del__(self):
        """Clean up WebDriver when object is destroyed"""
        try:
            self.cleanup()
            logger.debug("Successfully cleaned up WebDriver")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            
def print_stats_summary(stats: Optional[Dict[str, Any]]) -> None:
    """Print a summary of the collected statistics"""
    if not stats:
        logger.error("No statistics available to summarize")
        return
        
    try:
        logger.info("\nTeam Statistics Summary:")
        logger.info(f"Squad Players: {len(stats['players'])}")
        logger.info(f"Matches: {len(stats['matches'])}")
        
        # Count players by position
        positions = {}
        for player in stats['players'].values():
            pos = player.get('position', 'Unknown')
            positions[pos] = positions.get(pos, 0) + 1
            
        logger.info("\nPlayers by Position:")
        for pos, count in sorted(positions.items()):
            logger.info(f"{pos}: {count}")
            
    except Exception as e:
        logger.error(f"Error generating statistics summary: {str(e)}", exc_info=True)
        
if __name__ == "__main__":
    try:
        # Test the scraper with Liverpool's page
        scraper = TeamStatsScraper()
        liverpool_url = "https://fbref.com/en/squads/822bd0ba/Liverpool-Stats"
        stats = scraper.get_team_stats(liverpool_url)
        print_stats_summary(stats)
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
    finally:
        logger.info("Scraper execution completed")

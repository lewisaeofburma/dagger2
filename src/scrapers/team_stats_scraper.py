from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import sys
from pathlib import Path
import json
from datetime import datetime

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from scrapers.base_scraper import BaseScraper
from utils import get_logger
from utils.file_manager import FileManager

logger = get_logger('scraper.team_stats')

class TeamStatsScraper(BaseScraper):
    def __init__(self):
        """Initialize the Team Stats scraper"""
        super().__init__()
        self.file_manager = FileManager()
        
    def _extract_table_data(self, table, exclude_cols=None):
        """
        Extract data from a table
        
        Args:
            table: Selenium WebElement representing the table
            exclude_cols (list): List of column names to exclude
            
        Returns:
            list: List of dictionaries containing row data
        """
        if exclude_cols is None:
            exclude_cols = []
            
        try:
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr:not(.thead)")
            data = []
            
            for row in rows:
                row_data = {}
                cells = row.find_elements(By.CSS_SELECTOR, "td, th")
                
                for cell in cells:
                    stat = cell.get_attribute('data-stat')
                    if stat and stat not in exclude_cols:
                        value = cell.text.strip()
                        # Convert numeric values
                        try:
                            if '.' in value:
                                value = float(value)
                            elif value.isdigit():
                                value = int(value)
                            elif value.startswith('+') and value[1:].isdigit():
                                value = int(value)
                            elif value.startswith('-') and value[1:].isdigit():
                                value = int(value)
                            elif ',' in value:
                                value = float(value.replace(',', ''))
                        except ValueError:
                            pass
                        row_data[stat] = value
                        
                if row_data:  # Only add non-empty rows
                    data.append(row_data)
                    
            return data
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return []
            
    def get_team_stats(self, team_url):
        """
        Get comprehensive team statistics
        
        Args:
            team_url (str): URL of the team's page
            
        Returns:
            dict: Dictionary containing team statistics
        """
        logger.info(f"Fetching team statistics from: {team_url}")
        
        if not self.get_page(team_url):
            logger.error("Failed to load team page")
            return None
            
        try:
            team_data = {
                'url': team_url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'players': {},  # New section for player profiles
                'squad': {},
                'goalkeepers': {},
                'matches': [],
                'shooting': [],
                'passing': [],
                'pass_types': [],
                'goal_creation': [],
                'defense': [],
                'possession': [],
                'playing_time': [],
                'miscellaneous': []
            }
            
            # Squad Statistics (Standard)
            squad_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_standard_9")
            if squad_table:
                squad_stats = self._extract_table_data(
                    squad_table,
                    exclude_cols=['nationality']
                )
                team_data['squad']['standard'] = squad_stats
                
                # Create player profiles
                for player_stats in squad_stats:
                    if 'player' in player_stats:
                        player_name = player_stats['player']
                        team_data['players'][player_name] = {
                            'name': player_name,
                            'position': player_stats.get('position', ''),
                            'age': player_stats.get('age', ''),
                            'standard_stats': player_stats
                        }
                logger.info("Collected squad standard statistics")
            
            # Match Logs
            matches_table = self.wait_for_element(By.CSS_SELECTOR, "table#matchlogs_for")
            if matches_table:
                team_data['matches'] = self._extract_table_data(
                    matches_table,
                    exclude_cols=['notes']
                )
                logger.info(f"Collected {len(team_data['matches'])} match logs")
            
            # Goalkeeper Statistics
            gk_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_keeper_9")
            if gk_table:
                gk_stats = self._extract_table_data(
                    gk_table,
                    exclude_cols=['nationality']
                )
                team_data['goalkeepers']['standard'] = gk_stats
                
                # Add goalkeeper stats to player profiles
                for gk_stat in gk_stats:
                    if 'player' in gk_stat:
                        player_name = gk_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['goalkeeper_stats'] = gk_stat
                logger.info("Collected goalkeeper standard statistics")
                
            gk_adv_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_keeper_adv_9")
            if gk_adv_table:
                gk_adv_stats = self._extract_table_data(
                    gk_adv_table,
                    exclude_cols=['nationality']
                )
                team_data['goalkeepers']['advanced'] = gk_adv_stats
                
                # Add advanced goalkeeper stats to player profiles
                for gk_stat in gk_adv_stats:
                    if 'player' in gk_stat:
                        player_name = gk_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['goalkeeper_advanced_stats'] = gk_stat
                logger.info("Collected goalkeeper advanced statistics")
            
            # Shooting Statistics
            shooting_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_shooting_9")
            if shooting_table:
                shooting_stats = self._extract_table_data(
                    shooting_table,
                    exclude_cols=['nationality']
                )
                team_data['shooting'] = shooting_stats
                
                # Add shooting stats to player profiles
                for shoot_stat in shooting_stats:
                    if 'player' in shoot_stat:
                        player_name = shoot_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['shooting_stats'] = shoot_stat
                logger.info("Collected shooting statistics")
            
            # Passing Statistics
            passing_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_passing_9")
            if passing_table:
                passing_stats = self._extract_table_data(
                    passing_table,
                    exclude_cols=['nationality']
                )
                team_data['passing'] = passing_stats
                
                # Add passing stats to player profiles
                for pass_stat in passing_stats:
                    if 'player' in pass_stat:
                        player_name = pass_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['passing_stats'] = pass_stat
                logger.info("Collected passing statistics")
            
            # Pass Types
            pass_types_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_passing_types_9")
            if pass_types_table:
                pass_types_stats = self._extract_table_data(
                    pass_types_table,
                    exclude_cols=['nationality']
                )
                team_data['pass_types'] = pass_types_stats
                
                # Add pass types stats to player profiles
                for pass_type_stat in pass_types_stats:
                    if 'player' in pass_type_stat:
                        player_name = pass_type_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['pass_types_stats'] = pass_type_stat
                logger.info("Collected pass types statistics")
                
            # Goal Creation
            gca_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_gca_9")
            if gca_table:
                gca_stats = self._extract_table_data(
                    gca_table,
                    exclude_cols=['nationality']
                )
                team_data['goal_creation'] = gca_stats
                
                # Add goal creation stats to player profiles
                for gca_stat in gca_stats:
                    if 'player' in gca_stat:
                        player_name = gca_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['goal_creation_stats'] = gca_stat
                logger.info("Collected goal creation statistics")
                
            # Defense
            defense_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_defense_9")
            if defense_table:
                defense_stats = self._extract_table_data(
                    defense_table,
                    exclude_cols=['nationality']
                )
                team_data['defense'] = defense_stats
                
                # Add defensive stats to player profiles
                for def_stat in defense_stats:
                    if 'player' in def_stat:
                        player_name = def_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['defense_stats'] = def_stat
                logger.info("Collected defensive statistics")
                
            # Possession
            possession_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_possession_9")
            if possession_table:
                possession_stats = self._extract_table_data(
                    possession_table,
                    exclude_cols=['nationality']
                )
                team_data['possession'] = possession_stats
                
                # Add possession stats to player profiles
                for poss_stat in possession_stats:
                    if 'player' in poss_stat:
                        player_name = poss_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['possession_stats'] = poss_stat
                logger.info("Collected possession statistics")
                
            # Playing Time
            playing_time_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_playing_time_9")
            if playing_time_table:
                playing_time_stats = self._extract_table_data(
                    playing_time_table,
                    exclude_cols=['nationality']
                )
                team_data['playing_time'] = playing_time_stats
                
                # Add playing time stats to player profiles
                for time_stat in playing_time_stats:
                    if 'player' in time_stat:
                        player_name = time_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['playing_time_stats'] = time_stat
                logger.info("Collected playing time statistics")
                
            # Miscellaneous Stats
            misc_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_misc_9")
            if misc_table:
                misc_stats = self._extract_table_data(
                    misc_table,
                    exclude_cols=['nationality']
                )
                team_data['miscellaneous'] = misc_stats
                
                # Add miscellaneous stats to player profiles
                for misc_stat in misc_stats:
                    if 'player' in misc_stat:
                        player_name = misc_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['miscellaneous_stats'] = misc_stat
                logger.info("Collected miscellaneous statistics")
            
            # Save the data
            timestamp = datetime.now().strftime('%Y%m%d')
            team_name = team_url.split('/')[-2].lower()
            filename = f"{team_name}_stats_{timestamp}.json"
            
            self.file_manager.save_json(team_data, filename, 'teams')
            logger.info(f"Saved team statistics to {filename}")
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error fetching team statistics: {e}")
            return None
            
    def __del__(self):
        """Clean up WebDriver when object is destroyed"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
                
if __name__ == "__main__":
    # Test the scraper with Liverpool's page
    scraper = TeamStatsScraper()
    liverpool_url = "https://fbref.com/en/squads/822bd0ba/Liverpool-Stats"
    stats = scraper.get_team_stats(liverpool_url)
    
    if stats:
        logger.info("\nTeam Statistics Summary:")
        logger.info(f"Squad Players: {len(stats['squad'].get('standard', []))}")
        logger.info(f"Matches: {len(stats['matches'])}")
        logger.info(f"Goalkeepers: {len(stats['goalkeepers'].get('standard', []))}")
        logger.info(f"Players with shooting stats: {len(stats['shooting'])}")
        logger.info(f"Players with passing stats: {len(stats['passing'])}")
        logger.info(f"Players with pass types: {len(stats['pass_types'])}")
        logger.info(f"Players with goal creation stats: {len(stats['goal_creation'])}")
        logger.info(f"Players with defensive stats: {len(stats['defense'])}")
        logger.info(f"Players with possession stats: {len(stats['possession'])}")
        logger.info(f"Players with playing time stats: {len(stats['playing_time'])}")
        logger.info(f"Players with miscellaneous stats: {len(stats['miscellaneous'])}")

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
import sys
from pathlib import Path
import json
from datetime import datetime
import logging
from typing import Optional, Dict, List, Any, Union

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
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'players': {},  # All player stats will be stored here
                'matches': []   # Keep matches separate as it's team-level data
            }
            
            # Squad Statistics (Standard)
            squad_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_standard_9")
            if squad_table:
                squad_stats = self._extract_table_data(
                    squad_table,
                    exclude_cols=['nationality']
                )
                
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
                logger.info(f"Collected standard statistics for {len(squad_stats)} players")
            else:
                logger.warning("Squad statistics table not found")
            
            # Match Logs
            matches_table = self.wait_for_element(By.CSS_SELECTOR, "table#matchlogs_for")
            if matches_table:
                team_data['matches'] = self._extract_table_data(
                    matches_table,
                    exclude_cols=['notes']
                )
                logger.info(f"Collected {len(team_data['matches'])} match logs")
            else:
                logger.warning("Match logs table not found")
            
            # Goalkeeper Statistics
            gk_table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_keeper_9")
            if gk_table:
                gk_stats = self._extract_table_data(
                    gk_table,
                    exclude_cols=['nationality']
                )
                
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
                
                # Add miscellaneous stats to player profiles
                for misc_stat in misc_stats:
                    if 'player' in misc_stat:
                        player_name = misc_stat['player']
                        if player_name in team_data['players']:
                            team_data['players'][player_name]['miscellaneous_stats'] = misc_stat
                logger.info("Collected miscellaneous statistics")
            
            # After collecting all stats
            player_count = len(team_data['players'])
            logger.info(f"Successfully collected data for {player_count} players")
            
            # Save the data
            team_id = team_url.split('/')[-2]
            filename = f"{team_id}_stats_{datetime.now().strftime('%Y%m%d')}.json"
            
            try:
                self.file_manager.save_team_data(team_data, filename)
                logger.info(f"Saved team statistics to {filename}")
            except Exception as e:
                logger.error(f"Error saving team data: {str(e)}", exc_info=True)
            
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

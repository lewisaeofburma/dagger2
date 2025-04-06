"""
Team stats service for handling detailed team statistics
"""
import logging
from typing import Dict, Any, Optional, List, Union
from bs4 import BeautifulSoup
from datetime import datetime
import json

from .base_service import BaseService
from src.config import get_config
from src.utils.webdriver_pool import get_webdriver_pool

logger = logging.getLogger(__name__)


class TeamStatsService(BaseService):
    """Service for handling detailed team statistics."""

    def __init__(self):
        """Initialize the team stats service."""
        super().__init__()

    def get_team_stats(self, team_url: str, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive team statistics.

        Args:
            team_url: URL of the team's page
            team_name: Name of the team

        Returns:
            dict: Team statistics or None if error occurs
        """
        logger.info(f"Fetching team statistics from: {team_url}")

        try:
            # Analyze the page structure if debug is enabled
            if self.config.get('debug_enabled', False):
                from debug.html_analyzer import HTMLAnalyzer
                html_analyzer = HTMLAnalyzer()
                html_analyzer.analyze_page(team_url, save_html=True)

            # Get the page with rate limiting
            page_source = self.get_page_with_rate_limit(
                team_url, domain="fbref")
            if not page_source:
                logger.error("Failed to load team page")
                return None

            # Parse the page
            soup = BeautifulSoup(page_source, 'html.parser')

            # Initialize team data structure
            team_data = {
                'url': team_url,
                'name': team_name,
                'timestamp': self.get_timestamp(),
                'players': {},  # All player stats will be stored here
                'matches': []   # Keep matches separate as it's team-level data
            }

            # Process all statistics tables
            self._process_squad_statistics(soup, team_data)
            self._process_match_logs(soup, team_data)
            self._process_goalkeeper_statistics(soup, team_data)
            self._process_shooting_statistics(soup, team_data)
            self._process_passing_statistics(soup, team_data)
            self._process_pass_types(soup, team_data)
            self._process_goal_creation(soup, team_data)
            self._process_defense_statistics(soup, team_data)
            self._process_possession_statistics(soup, team_data)
            self._process_playing_time(soup, team_data)
            self._process_miscellaneous_stats(soup, team_data)

            # After collecting all stats
            player_count = len(team_data['players'])
            logger.info(
                f"Successfully collected data for {player_count} players")

            # Count players by position
            positions = {}
            for player in team_data['players'].values():
                pos = player.get('position', 'Unknown')
                positions[pos] = positions.get(pos, 0) + 1

            logger.info("\nPlayers by Position:")
            for pos, count in sorted(positions.items()):
                logger.info(f"{pos}: {count}")

            return team_data

        except Exception as e:
            logger.error(
                f"Error fetching team statistics: {str(e)}", exc_info=True)
            return None

    def _process_squad_statistics(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process squad statistics table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        squad_table = soup.find('table', {'id': 'stats_standard_9'})
        if squad_table:
            self._process_player_table(squad_table, team_data, 'stats')
        else:
            logger.warning("Squad statistics table not found")

    def _process_match_logs(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process match logs table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
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

    def _process_goalkeeper_statistics(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process goalkeeper statistics table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        gk_table = soup.find('table', {'id': 'stats_keeper_9'})
        if gk_table:
            self._process_player_table(gk_table, team_data, 'goalkeeper_stats')
        else:
            logger.warning("Goalkeeper statistics table not found")

    def _process_shooting_statistics(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process shooting statistics table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        shooting_table = soup.find('table', {'id': 'stats_shooting_9'})
        if shooting_table:
            self._process_player_table(
                shooting_table, team_data, 'shooting_stats')
        else:
            logger.warning("Shooting statistics table not found")

    def _process_passing_statistics(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process passing statistics table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        passing_table = soup.find('table', {'id': 'stats_passing_9'})
        if passing_table:
            self._process_player_table(
                passing_table, team_data, 'passing_stats')
        else:
            logger.warning("Passing statistics table not found")

    def _process_pass_types(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process pass types table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        pass_types_table = soup.find('table', {'id': 'stats_passing_types_9'})
        if pass_types_table:
            self._process_player_table(
                pass_types_table, team_data, 'pass_types_stats')
        else:
            logger.warning("Pass types statistics table not found")

    def _process_goal_creation(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process goal creation table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        gca_table = soup.find('table', {'id': 'stats_gca_9'})
        if gca_table:
            self._process_player_table(
                gca_table, team_data, 'goal_creation_stats')
        else:
            logger.warning("Goal creation statistics table not found")

    def _process_defense_statistics(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process defense statistics table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        defense_table = soup.find('table', {'id': 'stats_defense_9'})
        if defense_table:
            self._process_player_table(
                defense_table, team_data, 'defense_stats')
        else:
            logger.warning("Defense statistics table not found")

    def _process_possession_statistics(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process possession statistics table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        possession_table = soup.find('table', {'id': 'stats_possession_9'})
        if possession_table:
            self._process_player_table(
                possession_table, team_data, 'possession_stats')
        else:
            logger.warning("Possession statistics table not found")

    def _process_playing_time(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process playing time table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        playing_time_table = soup.find('table', {'id': 'stats_playing_time_9'})
        if playing_time_table:
            self._process_player_table(
                playing_time_table, team_data, 'playing_time_stats')
        else:
            logger.warning("Playing time statistics table not found")

    def _process_miscellaneous_stats(self, soup: BeautifulSoup, team_data: Dict[str, Any]) -> None:
        """
        Process miscellaneous statistics table.

        Args:
            soup: BeautifulSoup object
            team_data: Team data dictionary to update
        """
        misc_table = soup.find('table', {'id': 'stats_misc_9'})
        if misc_table:
            self._process_player_table(
                misc_table, team_data, 'miscellaneous_stats')
        else:
            logger.warning("Miscellaneous statistics table not found")

    def _process_player_table(self, table: BeautifulSoup, team_data: Dict[str, Any], stats_key: str) -> None:
        """
        Process a player statistics table.

        Args:
            table: BeautifulSoup table element
            team_data: Team data dictionary to update
            stats_key: Key to store the statistics under in the player dictionary
        """
        try:
            rows = table.find('tbody').find_all('tr')
            for row in rows:
                player_cell = row.find('th', {'data-stat': 'player'})
                if not player_cell or not player_cell.find('a'):
                    continue

                player_name = player_cell.find('a').text.strip()
                player_url = f"{self.config.get('fbref_base_url')}{player_cell.find('a')['href']}"

                # Get all stats for the player
                stats = {}
                for cell in row.find_all(['td', 'th']):
                    stat_name = cell.get('data-stat')
                    if stat_name:
                        stats[stat_name] = cell.text.strip()

                # Initialize player if not exists
                if player_name not in team_data['players']:
                    team_data['players'][player_name] = {
                        'url': player_url,
                        'position': stats.get('position', 'Unknown')
                    }

                # Add stats to player
                team_data['players'][player_name][stats_key] = stats

        except Exception as e:
            logger.error(f"Error processing {stats_key} table: {str(e)}")

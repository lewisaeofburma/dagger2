"""
League service for handling league-related operations
"""
import logging
from typing import Dict, Any, Optional, List, Union
from bs4 import BeautifulSoup
from datetime import datetime

from .base_service import BaseService
from src.config import get_config

logger = logging.getLogger(__name__)


class LeagueService(BaseService):
    """Service for handling league-related operations."""

    def __init__(self):
        """Initialize the league service."""
        super().__init__()
        self.base_url = self.config.get('premier_league_url')

    def get_league_standings(self) -> Optional[List[Dict[str, str]]]:
        """
        Get Premier League standings.

        Returns:
            list: List of dictionaries containing team standings, or None if error occurs
        """
        logger.info("Fetching Premier League standings...")

        try:
            page_source = self.get_page_with_rate_limit(
                self.base_url, domain="fbref")
            if not page_source:
                logger.error("Failed to load Premier League standings page")
                return None

            soup = BeautifulSoup(page_source, 'html.parser')

            # Find the standings table
            standings_table = soup.find(
                'table', {'id': 'results2024-202591_overall'})
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
                    team_data['draws'] = team_data.get(
                        'ties', '0')  # FBRef uses 'ties' for draws
                    team_data['losses'] = team_data.get('losses', '0')
                    team_data['goals_for'] = team_data.get('goals_for', '0')
                    team_data['goals_against'] = team_data.get(
                        'goals_against', '0')
                    team_data['goal_diff'] = team_data.get('goal_diff', '0')

                    # Extract team URL if available
                    team_cell = row.find('td', {'data-stat': 'team'})
                    if team_cell and team_cell.find('a'):
                        team_url = f"{self.config.get('fbref_base_url')}{team_cell.find('a')['href']}"
                        team_data['url'] = team_url
                        team_data['team_id'] = team_url.split('/')[-2]

                    standings.append(team_data)
                    logger.info(
                        f"Found team: {team_data['team']} - {team_data['points']} pts")

            if standings:
                logger.info(
                    f"Successfully found {len(standings)} teams in standings")

                # Save standings data
                timestamp = self.get_timestamp()
                filename = f'standings_{timestamp}.json'
                if self.save_data_with_retry(standings, filename, 'standings'):
                    logger.info("Standings data saved successfully")
                else:
                    logger.error("Failed to save standings data")

                return standings
            else:
                logger.error("No teams found in standings")
                return None

        except Exception as e:
            logger.error(
                f"Error fetching league standings: {str(e)}", exc_info=True)
            return None

    def get_team_stats(self) -> Optional[List[Dict[str, Union[str, float, int]]]]:
        """
        Get team statistics.

        Returns:
            list: List of dictionaries containing team statistics
        """
        logger.info("Fetching team statistics...")

        try:
            page_source = self.get_page_with_rate_limit(
                self.base_url, domain="fbref")
            if not page_source:
                logger.error("Failed to load team statistics page")
                return None

            soup = BeautifulSoup(page_source, 'html.parser')

            # Find the statistics table
            stats_table = soup.find(
                'table', {'id': 'stats_squads_standard_for'})
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
                                team_data[stat] = float(
                                    value) if '.' in value else int(value)
                            except ValueError:
                                pass

                    stats.append(team_data)
                    logger.info(
                        f"Found team statistics for {team_data['team']}")

            if stats:
                logger.info(
                    f"Successfully found statistics for {len(stats)} teams")

                # Save team stats data
                timestamp = self.get_timestamp()
                filename = f'team_stats_{timestamp}.json'
                if self.save_data_with_retry(stats, filename, 'stats'):
                    logger.info("Team statistics data saved successfully")
                else:
                    logger.error("Failed to save team statistics data")

                return stats
            else:
                logger.error("No team statistics found")
                return None

        except Exception as e:
            logger.error(
                f"Error fetching team statistics: {str(e)}", exc_info=True)
            return None

    def get_league_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the league including standings and team statistics.

        Returns:
            dict: Dictionary containing league summary
        """
        standings = self.get_league_standings()
        team_stats = self.get_team_stats()

        return {
            'standings': standings if standings else [],
            'team_stats': team_stats if team_stats else [],
            'timestamp': self.get_timestamp(),
            'league': 'Premier League',
            'season': '2024-2025'
        }

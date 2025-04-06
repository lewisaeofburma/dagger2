"""
Team service for handling team-related operations
"""
import logging
from typing import Dict, Any, Optional, List, Union
from bs4 import BeautifulSoup
from datetime import datetime
import json

from .base_service import BaseService
from src.config import get_config

logger = logging.getLogger(__name__)


class TeamService(BaseService):
    """Service for handling team-related operations."""

    def __init__(self):
        """Initialize the team service."""
        super().__init__()
        self.base_url = self.config.get('premier_league_url')

    def get_premier_league_teams(self) -> Optional[List[Dict[str, str]]]:
        """
        Fetch Premier League teams.

        Returns:
            list: List of dictionaries containing team information or None if error occurs
        """
        logger.info(f"Fetching Premier League teams from: {self.base_url}")

        try:
            page_source = self.get_page_with_rate_limit(
                self.base_url, domain="fbref")
            if not page_source:
                logger.error("Failed to load Premier League stats page")
                return None

            soup = BeautifulSoup(page_source, 'html.parser')

            # Find the table containing team data
            teams_table = soup.find(
                'table', {'id': 'results2024-202591_overall'})
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
                        team_url = f"{self.config.get('fbref_base_url')}{team_link['href']}"
                        # Extract team ID from URL
                        team_id = team_url.split('/')[-2]

                        teams.append({
                            'name': team_name,
                            'url': team_url,
                            'id': team_id
                        })
                        logger.info(f"Found team: {team_name}")

            if teams:
                logger.info(f"Successfully found {len(teams)} teams")

                # Save teams data
                timestamp = self.get_timestamp()
                filename = f'teams_{timestamp}.json'
                if self.save_data_with_retry(teams, filename, 'teams'):
                    logger.info("Teams data saved successfully")
                else:
                    logger.error("Failed to save teams data")

                return teams
            else:
                logger.error("No teams found in the table")
                return None

        except Exception as e:
            logger.error(
                f"Error fetching Premier League teams: {str(e)}", exc_info=True)
            return None

    def get_team_by_name(self, team_name: str, teams: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, str]]:
        """
        Get team information by name.

        Args:
            team_name: Name of the team
            teams: List of teams (if None, will fetch teams)

        Returns:
            dict: Team information or None if not found
        """
        if not teams:
            teams = self.get_premier_league_teams()
            if not teams:
                return None

        # Case-insensitive partial match
        team_name_lower = team_name.lower()
        for team in teams:
            if team_name_lower in team['name'].lower():
                return team

        logger.warning(f"Team not found: {team_name}")
        return None

    def get_all_teams_detailed_stats(self, teams: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Get detailed statistics for all teams or specified teams.

        Args:
            teams: List of teams to get stats for (if None, will fetch all teams)

        Returns:
            dict: Dictionary mapping team IDs to their statistics
        """
        if not teams:
            teams = self.get_premier_league_teams()
            if not teams:
                logger.error("Could not fetch teams")
                return {}

        # Get teams to analyze from config
        teams_to_analyze = self.config.get('teams_to_analyze', [])

        # If teams_to_analyze is empty, analyze all teams
        if not teams_to_analyze:
            teams_to_analyze = [team['name'] for team in teams]

        team_stats = {}
        timestamp = self.get_timestamp()

        for team in teams:
            if any(team_filter.lower() in team['name'].lower() for team_filter in teams_to_analyze):
                logger.info(
                    f"\nFetching detailed statistics for team: {team['name']}")

                # Check if we already have recent data for this team
                team_id = team['id']
                recent_file = f"{team_id}_{timestamp}.json"

                # Try to load from existing file first
                stats = self.load_data(recent_file, 'teams')

                # If not found, fetch new data
                if not stats:
                    from .team_stats_service import TeamStatsService
                    team_stats_service = TeamStatsService()
                    stats = team_stats_service.get_team_stats(
                        team['url'], team['name'])

                    if stats:
                        # Save the data
                        filename = f"{team_id}_{timestamp}.json"
                        if self.save_data_with_retry(stats, filename, 'teams'):
                            logger.info(
                                f"{team['name']} detailed statistics saved successfully")
                        else:
                            logger.error(
                                f"Failed to save {team['name']} statistics")

                if stats:
                    team_stats[team_id] = stats

        return team_stats

    def get_team_detailed_stats(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a specific team.

        Args:
            team_name: Name of the team

        Returns:
            dict: Team statistics or None if error occurs
        """
        teams = self.get_premier_league_teams()
        if not teams:
            logger.error("Could not fetch teams")
            return None

        team = self.get_team_by_name(team_name, teams)
        if not team:
            logger.error(f"Team not found: {team_name}")
            return None

        logger.info(f"\nFetching detailed statistics for team: {team['name']}")

        # Check if we already have recent data for this team
        team_id = team['id']
        timestamp = self.get_timestamp()
        recent_file = f"{team_id}_{timestamp}.json"

        # Try to load from existing file first
        stats = self.load_data(recent_file, 'teams')

        # If not found, fetch new data
        if not stats:
            from .team_stats_service import TeamStatsService
            team_stats_service = TeamStatsService()
            stats = team_stats_service.get_team_stats(
                team['url'], team['name'])

            if stats:
                # Save the data
                filename = f"{team_id}_{timestamp}.json"
                if self.save_data_with_retry(stats, filename, 'teams'):
                    logger.info(
                        f"{team['name']} detailed statistics saved successfully")
                else:
                    logger.error(f"Failed to save {team['name']} statistics")

        return stats

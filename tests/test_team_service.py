"""
Unit tests for the TeamService class
"""
from services.team_service import TeamService
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Use relative imports for better compatibility


class TestTeamService(unittest.TestCase):
    """Test cases for TeamService."""

    def setUp(self):
        """Set up test fixtures."""
        self.team_service = TeamService()

        # Sample data for testing
        self.sample_teams = [
            {
                'name': 'Liverpool',
                'url': 'https://fbref.com/en/squads/822bd0ba/Liverpool-Stats',
                'id': '822bd0ba'
            },
            {
                'name': 'Arsenal',
                'url': 'https://fbref.com/en/squads/18bb7c10/Arsenal-Stats',
                'id': '18bb7c10'
            },
            {
                'name': 'Manchester City',
                'url': 'https://fbref.com/en/squads/b8fd03ef/Manchester-City-Stats',
                'id': 'b8fd03ef'
            }
        ]

    @patch('services.team_service.TeamService.get_page_with_rate_limit')
    def test_get_premier_league_teams_success(self, mock_get_page):
        """Test successful retrieval of Premier League teams."""
        # Mock the HTML content
        with open(os.path.join(project_root, 'tests/fixtures/premier_league_page.html'), 'r', encoding='utf-8') as f:
            mock_get_page.return_value = f.read()

        # Mock save_data_with_retry to return True
        self.team_service.save_data_with_retry = MagicMock(return_value=True)

        # Call the method
        teams = self.team_service.get_premier_league_teams()

        # Assertions
        self.assertIsNotNone(teams)
        self.assertIsInstance(teams, list)
        self.assertTrue(len(teams) > 0)

        # Check team structure
        for team in teams:
            self.assertIn('name', team)
            self.assertIn('url', team)
            self.assertIn('id', team)

    @patch('services.team_service.TeamService.get_page_with_rate_limit')
    def test_get_premier_league_teams_failure(self, mock_get_page):
        """Test failure to retrieve Premier League teams."""
        # Mock the get_page_with_rate_limit to return None
        mock_get_page.return_value = None

        # Call the method
        teams = self.team_service.get_premier_league_teams()

        # Assertions
        self.assertIsNone(teams)

    def test_get_team_by_name_exact_match(self):
        """Test getting a team by exact name match."""
        # Call the method
        team = self.team_service.get_team_by_name(
            'Liverpool', self.sample_teams)

        # Assertions
        self.assertIsNotNone(team)
        self.assertEqual(team['name'], 'Liverpool')
        self.assertEqual(team['id'], '822bd0ba')

    def test_get_team_by_name_partial_match(self):
        """Test getting a team by partial name match."""
        # Call the method
        team = self.team_service.get_team_by_name('City', self.sample_teams)

        # Assertions
        self.assertIsNotNone(team)
        self.assertEqual(team['name'], 'Manchester City')
        self.assertEqual(team['id'], 'b8fd03ef')

    def test_get_team_by_name_no_match(self):
        """Test getting a team with no match."""
        # Call the method
        team = self.team_service.get_team_by_name(
            'Tottenham', self.sample_teams)

        # Assertions
        self.assertIsNone(team)

    @patch('services.team_service.TeamService.get_premier_league_teams')
    @patch('services.team_stats_service.TeamStatsService.get_team_stats')
    def test_get_team_detailed_stats(self, mock_get_team_stats, mock_get_teams):
        """Test getting detailed team statistics."""
        # Mock the get_premier_league_teams to return sample teams
        mock_get_teams.return_value = self.sample_teams

        # Mock the get_team_stats to return sample stats
        sample_stats = {
            'url': 'https://fbref.com/en/squads/822bd0ba/Liverpool-Stats',
            'name': 'Liverpool',
            'timestamp': '20250407',
            'players': {
                'Mohamed Salah': {
                    'url': 'https://fbref.com/en/players/e342ad68/Mohamed-Salah',
                    'position': 'FW',
                    'stats': {
                        'goals': '20',
                        'assists': '10'
                    }
                }
            },
            'matches': []
        }
        mock_get_team_stats.return_value = sample_stats

        # Mock save_data_with_retry to return True
        self.team_service.save_data_with_retry = MagicMock(return_value=True)

        # Call the method
        stats = self.team_service.get_team_detailed_stats('Liverpool')

        # Assertions
        self.assertIsNotNone(stats)
        self.assertEqual(stats['name'], 'Liverpool')
        self.assertIn('players', stats)
        self.assertIn('Mohamed Salah', stats['players'])
        self.assertEqual(stats['players']['Mohamed Salah']['position'], 'FW')


if __name__ == '__main__':
    unittest.main()

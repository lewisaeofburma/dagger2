"""
Main module for the football analysis application.
Uses the improved architecture with services, configuration, and better error handling.
"""
from src.config import get_config
from src.services import TeamService, TeamStatsService, LeagueService
from src.utils import get_logger
from src.utils.webdriver_pool import get_webdriver_pool
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to Python path to enable relative imports
import os
import sys
from pathlib import Path

# Get the project root directory
project_root = str(Path(__file__).resolve().parent.parent)

# Add to Python path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Football Analysis Application')
    parser.add_argument('--team', type=str,
                        help='Team to analyze (default: all teams)')
    parser.add_argument('--standings', action='store_true',
                        help='Fetch league standings')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode')
    return parser.parse_args()


def main():
    """Main function to run the football analysis application."""
    # Parse command line arguments
    args = parse_arguments()

    # Configure logging
    logger = get_logger('main')
    logger.info("Starting football analysis application")

    # Get configuration
    config = get_config()

    # Update configuration based on command line arguments
    if args.debug:
        config.set('debug_enabled', True)

    if args.headless:
        webdriver_settings = config.get('webdriver_settings', {})
        webdriver_settings['headless'] = True
        config.set('webdriver_settings', webdriver_settings)

    # Initialize services
    team_service = TeamService()
    team_stats_service = TeamStatsService()
    league_service = LeagueService()

    try:
        # Get Premier League teams
        logger.info("Fetching Premier League teams...")
        teams = team_service.get_premier_league_teams()

        if not teams:
            logger.error("No teams were found")
            return

        logger.info("\nPremier League Teams:")
        for team in teams:
            logger.info(f"- {team['name']}")

        # Get team statistics
        if args.team:
            # Get statistics for a specific team
            team_name = args.team
            logger.info(
                f"\nFetching detailed statistics for team: {team_name}")
            team_stats = team_service.get_team_detailed_stats(team_name)

            if not team_stats:
                logger.error(f"Failed to get statistics for {team_name}")
        else:
            # Get statistics for all teams or teams specified in config
            teams_to_analyze = config.get('teams_to_analyze', [])

            if teams_to_analyze:
                logger.info(
                    f"\nFetching detailed statistics for specified teams: {', '.join(teams_to_analyze)}")
            else:
                logger.info("\nFetching detailed statistics for all teams")

            team_stats = team_service.get_all_teams_detailed_stats(teams)

            if not team_stats:
                logger.error("Failed to get team statistics")

        # Get league standings if requested
        if args.standings or not args.team:
            logger.info("\nFetching Premier League standings...")
            standings = league_service.get_league_standings()

            if standings:
                logger.info("\nPremier League Standings:")
                for team in standings:
                    logger.info(f"{team['rank']}. {team['team']} - {team['points']} pts "
                                f"(W: {team['wins']}, D: {team['draws']}, L: {team['losses']})")
            else:
                logger.error("Failed to get league standings")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)

    finally:
        # Clean up resources
        webdriver_pool = get_webdriver_pool()
        webdriver_pool.close_all()
        logger.info("Application execution completed")


if __name__ == "__main__":
    main()

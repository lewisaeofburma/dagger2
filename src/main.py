import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

# Add project root to Python path for debug module
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from scrapers import FBRefScraper, LeagueStatsScraper
from scrapers.team_stats_scraper import TeamStatsScraper
from utils import get_logger
from utils.file_manager import FileManager
from debug.html_analyzer import HTMLAnalyzer

def get_team_detailed_stats(team_url: str, team_scraper: TeamStatsScraper, logger) -> Optional[Dict[str, Any]]:
    """
    Get detailed statistics for a specific team
    
    Args:
        team_url: URL of the team's page
        team_scraper: TeamStatsScraper instance
        logger: Logger instance
        
    Returns:
        Dictionary containing team statistics or None if error occurs
    """
    try:
        logger.info(f"\nFetching detailed statistics for team: {team_url}")
        stats = team_scraper.get_team_stats(team_url)
        
        if stats:
            logger.info("Team Statistics Summary:")
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
                
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching detailed team statistics: {str(e)}", exc_info=True)
        return None

def main():
    """Main function to run the football analysis application"""
    logger = get_logger('main')
    logger.info("Starting football analysis application")
    
    # Initialize components
    teams_scraper = FBRefScraper()
    league_scraper = LeagueStatsScraper()
    team_stats_scraper = TeamStatsScraper()
    file_manager = FileManager()
    html_analyzer = HTMLAnalyzer()  # For debugging purposes
    
    try:
        # Get Premier League teams
        logger.info("Fetching Premier League teams...")
        teams = teams_scraper.get_premier_league_teams()
        
        if teams:
            logger.info("\nPremier League Teams:")
            for team in teams:
                logger.info(f"- {team['name']}")
                
            # Save teams data
            timestamp = datetime.now().strftime('%Y%m%d')
            file_manager.save_json(teams, f'teams_{timestamp}.json', 'teams')
            logger.info("Teams data saved successfully")
            
            # Get detailed stats for Liverpool (as an example)
            liverpool_team = next((team for team in teams if 'Liverpool' in team['name']), None)
            if liverpool_team:
                liverpool_stats = get_team_detailed_stats(
                    liverpool_team['url'],
                    team_stats_scraper,
                    logger
                )
                if liverpool_stats:
                    logger.info("Liverpool detailed statistics saved successfully")
        else:
            logger.error("No teams were found")
            return
        
        # Get Premier League standings
        logger.info("\nFetching Premier League standings...")
        standings = league_scraper.get_league_standings()
        if standings:
            logger.info("\nPremier League Standings:")
            for team in standings:
                logger.info(f"{team['rank']}. {team['team']} - {team['points']} pts "
                          f"(W: {team['wins']}, D: {team['draws']}, L: {team['losses']})")
                          
            # Save standings data
            file_manager.save_json(standings, f'standings_{timestamp}.json', 'standings')
            logger.info("Standings data saved successfully")
        
        # Get team statistics
        logger.info("\nFetching team statistics...")
        stats = league_scraper.get_team_stats()
        if stats:
            logger.info("\nTeam Statistics:")
            for team in stats:
                logger.info(f"{team['team']} - Goals: {team.get('goals', 'N/A')}, "
                          f"Shots: {team.get('shots', 'N/A')}, "
                          f"Possession: {team.get('possession', 'N/A')}%")
                          
            # Save statistics data
            file_manager.save_json(stats, f'stats_{timestamp}.json', 'stats')
            logger.info("Team statistics saved successfully")
            
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        
    finally:
        # Clean up resources
        team_stats_scraper.cleanup()
        logger.info("Application execution completed")

if __name__ == "__main__":
    main()

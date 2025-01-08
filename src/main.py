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

def get_team_detailed_stats(team_url: str, team_name: str, team_scraper: TeamStatsScraper, logger) -> Optional[Dict[str, Any]]:
    """
    Get detailed statistics for a specific team
    
    Args:
        team_url: URL of the team's page
        team_name: Name of the team
        team_scraper: TeamStatsScraper instance
        logger: Logger instance
        
    Returns:
        Dictionary containing team statistics or None if error occurs
    """
    try:
        logger.info(f"\nFetching detailed statistics for team: {team_name}")
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

def save_data_with_retry(file_manager: FileManager, data: Dict[str, Any], filename: str, category: str, max_retries: int = 3) -> bool:
    """
    Save data with retry logic
    
    Args:
        file_manager: FileManager instance
        data: Data to save
        filename: Name of the file
        category: Category of data
        max_retries: Maximum number of retries
        
    Returns:
        bool: True if save was successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            result = file_manager.save_data(data, filename, category)
            if result:
                return True
            if attempt < max_retries - 1:
                logger.warning(f"Retrying save attempt {attempt + 1} of {max_retries}")
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Save attempt {attempt + 1} failed: {str(e)}. Retrying...")
            else:
                logger.error(f"All save attempts failed for {filename}")
    return False

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
            if save_data_with_retry(file_manager, teams, f'teams_{timestamp}.json', 'teams'):
                logger.info("Teams data saved successfully")
            else:
                logger.error("Failed to save teams data")
            
            # Get detailed stats for Liverpool
            liverpool_team = next((team for team in teams if 'Liverpool' in team['name']), None)
            if liverpool_team:
                liverpool_stats = get_team_detailed_stats(
                    liverpool_team['url'],
                    liverpool_team['name'],
                    team_stats_scraper,
                    logger
                )
                if liverpool_stats:
                    # Save Liverpool stats with consistent naming
                    team_id = liverpool_team['url'].split('/')[-2]  # Get team ID from URL
                    filename = f"{team_id}_{timestamp}.json"  # Use team ID for filename
                    if save_data_with_retry(file_manager, liverpool_stats, filename, 'teams'):
                        logger.info(f"{liverpool_team['name']} detailed statistics saved successfully")
                    else:
                        logger.error(f"Failed to save {liverpool_team['name']} statistics")
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
            if save_data_with_retry(file_manager, standings, f'standings_{timestamp}.json', 'standings'):
                logger.info("Standings data saved successfully")
            else:
                logger.error("Failed to save standings data")
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}", exc_info=True)
        
    finally:
        # Clean up resources
        teams_scraper.cleanup()
        league_scraper.cleanup()
        team_stats_scraper.cleanup()
        logger.info("Application execution completed")

if __name__ == "__main__":
    main()

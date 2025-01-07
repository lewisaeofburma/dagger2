import sys
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from scrapers import FBRefScraper, LeagueStatsScraper
from utils import get_logger
from utils.file_manager import FileManager

def main():
    """Main function to run the football analysis application"""
    logger = get_logger('main')
    logger.info("Starting football analysis application")
    
    # Initialize scrapers and file manager
    teams_scraper = FBRefScraper()
    league_scraper = LeagueStatsScraper()
    file_manager = FileManager()
    
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
    else:
        logger.error("No teams were found")
        return
    
    # Get Premier League standings
    logger.info("\nFetching Premier League standings...")
    try:
        standings = league_scraper.get_league_standings()
        if standings:
            logger.info("\nPremier League Standings:")
            for team in standings:
                logger.info(f"{team['rank']}. {team['team']} - {team['points']} pts "
                          f"(W: {team['wins']}, D: {team['draws']}, L: {team['losses']})")
                          
            # Save standings data
            file_manager.save_json(standings, f'standings_{timestamp}.json', 'standings')
            logger.info("Standings data saved successfully")
    except Exception as e:
        logger.error(f"Error fetching standings: {e}")
    
    # Get team statistics
    logger.info("\nFetching team statistics...")
    try:
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
        logger.error(f"Error fetching team statistics: {e}")

if __name__ == "__main__":
    main()

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from scrapers.base_scraper import BaseScraper
from utils import get_logger

logger = get_logger('scraper.league_stats')

class LeagueStatsScraper(BaseScraper):
    def __init__(self):
        """Initialize the League Stats scraper"""
        super().__init__()
        self.base_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
        
    def get_league_standings(self):
        """
        Get Premier League standings
        
        Returns:
            list: List of dictionaries containing team standings
        """
        logger.info("Fetching Premier League standings...")
        
        if not self.get_page(self.base_url):
            logger.error("Failed to load Premier League standings page")
            return None
            
        try:
            standings = []
            table = self.wait_for_element(By.CSS_SELECTOR, "table#results2024-202591_overall")
            
            if not table:
                logger.error("Could not find standings table")
                return None
                
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr:not(.spacer):not(.thead)")
            
            for row in rows:
                try:
                    rank = row.find_element(By.CSS_SELECTOR, "th[data-stat='rank']").text.strip()
                    team = row.find_element(By.CSS_SELECTOR, "td[data-stat='team']").text.strip()
                    points = row.find_element(By.CSS_SELECTOR, "td[data-stat='points']").text.strip()
                    wins = row.find_element(By.CSS_SELECTOR, "td[data-stat='wins']").text.strip()
                    draws = row.find_element(By.CSS_SELECTOR, "td[data-stat='ties']").text.strip()
                    losses = row.find_element(By.CSS_SELECTOR, "td[data-stat='losses']").text.strip()
                    goals_for = row.find_element(By.CSS_SELECTOR, "td[data-stat='goals_for']").text.strip()
                    goals_against = row.find_element(By.CSS_SELECTOR, "td[data-stat='goals_against']").text.strip()
                    goal_diff = row.find_element(By.CSS_SELECTOR, "td[data-stat='goal_diff']").text.strip()
                    
                    standings.append({
                        'rank': int(rank),
                        'team': team,
                        'points': int(points),
                        'wins': int(wins),
                        'draws': int(draws),
                        'losses': int(losses),
                        'goals_for': int(goals_for),
                        'goals_against': int(goals_against),
                        'goal_diff': int(goal_diff)
                    })
                    logger.info(f"Found standings for {team}")
                except NoSuchElementException:
                    logger.warning("Skipping row with missing data")
                    continue
                except ValueError as e:
                    logger.error(f"Error converting data: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing standings row: {e}")
                    continue
            
            if not standings:
                logger.error("No standings data found")
            else:
                logger.info(f"Successfully found standings for {len(standings)} teams")
                
            return standings
            
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            return None
                
    def get_team_stats(self):
        """
        Get team statistics
        
        Returns:
            list: List of dictionaries containing team statistics
        """
        logger.info("Fetching team statistics...")
        
        if not self.get_page(self.base_url):
            logger.error("Failed to load team statistics page")
            return None
            
        try:
            stats = []
            table = self.wait_for_element(By.CSS_SELECTOR, "table#stats_squads_standard_for")
            
            if not table:
                logger.error("Could not find statistics table")
                return None
                
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr:not(.spacer):not(.thead)")
            
            for row in rows:
                try:
                    team = row.find_element(By.CSS_SELECTOR, "th[data-stat='team']").text.strip()
                    possession = row.find_element(By.CSS_SELECTOR, "td[data-stat='possession']").text.strip()
                    goals = row.find_element(By.CSS_SELECTOR, "td[data-stat='goals']").text.strip()
                    assists = row.find_element(By.CSS_SELECTOR, "td[data-stat='assists']").text.strip()
                    xg = row.find_element(By.CSS_SELECTOR, "td[data-stat='xg']").text.strip()
                    xg_assist = row.find_element(By.CSS_SELECTOR, "td[data-stat='xg_assist']").text.strip()
                    
                    stats.append({
                        'team': team,
                        'possession': float(possession) if possession else 0,
                        'goals': int(goals) if goals else 0,
                        'assists': int(assists) if assists else 0,
                        'xg': float(xg) if xg else 0,
                        'xg_assist': float(xg_assist) if xg_assist else 0
                    })
                    logger.info(f"Found statistics for {team}")
                except NoSuchElementException:
                    logger.warning("Skipping row with missing statistics")
                    continue
                except ValueError as e:
                    logger.error(f"Error converting statistics: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing statistics row: {e}")
                    continue
            
            if not stats:
                logger.error("No team statistics found")
            else:
                logger.info(f"Successfully found statistics for {len(stats)} teams")
                
            return stats
            
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

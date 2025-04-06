import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_dir: str):
        """
        Initialize the DataProcessor with the data directory path.
        
        Args:
            data_dir: Path to the directory containing team and standings data
        """
        self.data_dir = data_dir
        self.teams_dir = os.path.join(data_dir, 'teams')
        self.standings_dir = os.path.join(data_dir, 'standings')
        self.teams_info = self._load_teams_info()
        
    def _load_teams_info(self) -> Dict[str, str]:
        """Load teams info from teams_YYYYMMDD.json"""
        teams_info = {}
        for filename in os.listdir(self.teams_dir):
            if filename.startswith('teams_') and filename.endswith('.json'):
                file_path = os.path.join(self.teams_dir, filename)
                with open(file_path, 'r') as f:
                    teams_data = json.load(f)
                    for team in teams_data:
                        team_id = team['url'].split('/')[-2].split('-')[0]
                        teams_info[team_id] = team['name']
        return teams_info
    
    def load_team_data(self) -> Dict:
        """Load all individual team data from JSON files"""
        team_data = {}
        for filename in os.listdir(self.teams_dir):
            if '_202' in filename and filename.endswith('.json'):  # Match pattern like 822bd0ba_20250109.json
                file_path = os.path.join(self.teams_dir, filename)
                with open(file_path, 'r') as f:
                    team_data[filename] = json.load(f)
        return team_data
    
    def load_standings_data(self) -> Dict:
        """Load all standings data from JSON files"""
        standings_data = {}
        for filename in os.listdir(self.standings_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.standings_dir, filename)
                with open(file_path, 'r') as f:
                    standings_data[filename] = json.load(f)
        return standings_data
    
    def process_player_stats(self, team_data: Dict) -> pd.DataFrame:
        """
        Process player statistics into a DataFrame
        
        Args:
            team_data: Dictionary containing team data
            
        Returns:
            DataFrame with processed player statistics
        """
        all_players = []
        
        for team_file, team_info in team_data.items():
            team_id = team_file.split('_')[0]
            team_name = self.teams_info.get(team_id, '')
            
            for player_name, player_info in team_info.get('players', {}).items():
                # Basic stats
                player_dict = {
                    'team_id': team_id,
                    'team_name': team_name,
                    'player_name': player_name,
                    'player_url': player_info.get('url', ''),
                }
                
                # Add regular stats
                stats = player_info.get('stats', {})
                if stats:
                    player_dict.update({
                        'position': stats.get('position', ''),
                        'nationality': stats.get('nationality', '').split()[-1] if stats.get('nationality') else '',
                        'age': self._convert_age(stats.get('age', '')),
                    })
                    
                    for key, value in stats.items():
                        if key not in ['player', 'nationality', 'position', 'age']:
                            player_dict[f'stat_{key}'] = self._convert_stat(value)
                
                # Add defensive stats if available
                defense_stats = player_info.get('defense_stats', {})
                if defense_stats:
                    for key, value in defense_stats.items():
                        if key not in ['player', 'nationality', 'position', 'age']:
                            player_dict[f'defense_{key}'] = self._convert_stat(value)
                
                # Add possession stats if available
                possession_stats = player_info.get('possession_stats', {})
                if possession_stats:
                    for key, value in possession_stats.items():
                        if key not in ['player', 'nationality', 'position', 'age']:
                            player_dict[f'possession_{key}'] = self._convert_stat(value)
                
                # Add goal creation stats if available
                goal_creation_stats = player_info.get('goal_creation_stats', {})
                if goal_creation_stats:
                    for key, value in goal_creation_stats.items():
                        if key not in ['player', 'nationality', 'position', 'age']:
                            player_dict[f'creation_{key}'] = self._convert_stat(value)
                
                all_players.append(player_dict)
        
        return pd.DataFrame(all_players)
    
    def process_team_matches(self, team_data: Dict) -> pd.DataFrame:
        """
        Process team matches into a DataFrame
        
        Args:
            team_data: Dictionary containing team data
            
        Returns:
            DataFrame with processed match data
        """
        all_matches = []
        
        for team_file, team_info in team_data.items():
            team_id = team_file.split('_')[0]
            team_name = self.teams_info.get(team_id, '')
            
            for match in team_info.get('matches', []):
                match_dict = {
                    'team_id': team_id,
                    'team_name': team_name,
                    'date': match.get('date', ''),
                    'competition': match.get('comp', ''),
                    'round': match.get('round', ''),
                    'venue': match.get('venue', ''),
                    'result': match.get('result', ''),
                    'goals_for': self._convert_stat(match.get('goals_for', 0)),
                    'goals_against': self._convert_stat(match.get('goals_against', 0)),
                    'opponent': match.get('opponent', ''),
                    'opponent_id': match.get('opponent_id', ''),
                    'xg_for': self._convert_stat(match.get('xg_for', 0)),
                    'xg_against': self._convert_stat(match.get('xg_against', 0)),
                    'possession': self._convert_stat(match.get('possession', 0)),
                    'attendance': self._convert_stat(match.get('attendance', 0)),
                    'captain': match.get('captain', ''),
                    'formation': match.get('formation', ''),
                    'referee': match.get('referee', '')
                }
                all_matches.append(match_dict)
        
        matches_df = pd.DataFrame(all_matches)
        matches_df['date'] = pd.to_datetime(matches_df['date'])
        return matches_df
    
    def process_standings(self, standings_data: Dict) -> pd.DataFrame:
        """
        Process standings data into a DataFrame
        
        Args:
            standings_data: Dictionary containing standings data
            
        Returns:
            DataFrame with processed standings
        """
        all_standings = []
        
        for file, data in standings_data.items():
            timestamp = file.split('_')[1].split('.')[0]
            for team in data.get('standings', []):
                team_dict = {
                    'timestamp': timestamp,
                    'rank': team.get('rank', 0),
                    'team': team.get('team', ''),
                    'played': team.get('played', 0),
                    'wins': team.get('wins', 0),
                    'draws': team.get('draws', 0),
                    'losses': team.get('losses', 0),
                    'goals_for': team.get('goals_for', 0),
                    'goals_against': team.get('goals_against', 0),
                    'goal_diff': team.get('goal_diff', 0),
                    'points': team.get('points', 0),
                    'xg_for': self._convert_stat(team.get('xg_for', 0)),
                    'xg_against': self._convert_stat(team.get('xg_against', 0)),
                    'xg_diff': self._convert_stat(team.get('xg_diff', 0)),
                    'last_5': team.get('last_5', ''),
                    'attendance': self._convert_stat(team.get('attendance', 0)),
                    'top_team_scorers': team.get('top_team_scorers', ''),
                    'top_keeper': team.get('top_keeper', '')
                }
                all_standings.append(team_dict)
        
        standings_df = pd.DataFrame(all_standings)
        return standings_df
    
    def create_analysis_features(self, players_df: pd.DataFrame, matches_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create additional features for analysis
        
        Args:
            players_df: DataFrame with player statistics
            matches_df: DataFrame with match data
            
        Returns:
            DataFrame with additional features
        """
        # Add team performance metrics
        team_performance = matches_df[matches_df['competition'] == 'Premier League'].groupby('team_id').agg({
            'goals_for': 'mean',
            'goals_against': 'mean',
            'result': lambda x: (x == 'W').mean(),  # Win rate
            'xg_for': 'mean',
            'xg_against': 'mean',
            'possession': 'mean'
        }).reset_index()
        
        team_performance.columns = ['team_id', 'avg_goals_scored', 'avg_goals_conceded', 'win_rate', 
                                  'avg_xg_for', 'avg_xg_against', 'avg_possession']
        
        # Merge with player statistics
        analysis_df = players_df.merge(team_performance, on='team_id', how='left')
        
        # Create position-specific features
        analysis_df['is_forward'] = analysis_df['position'].str.contains('FW').fillna(False)
        analysis_df['is_midfielder'] = analysis_df['position'].str.contains('MF').fillna(False)
        analysis_df['is_defender'] = analysis_df['position'].str.contains('DF').fillna(False)
        analysis_df['is_goalkeeper'] = analysis_df['position'].str.contains('GK').fillna(False)
        
        # Calculate efficiency metrics
        minutes_90s = analysis_df['stat_minutes_90s'].fillna(90)
        analysis_df['goals_per_90'] = analysis_df['stat_goals'].fillna(0) / minutes_90s
        analysis_df['assists_per_90'] = analysis_df['stat_assists'].fillna(0) / minutes_90s
        analysis_df['goal_contributions_per_90'] = analysis_df['goals_per_90'] + analysis_df['assists_per_90']
        
        # Calculate defensive metrics
        analysis_df['tackles_won_pct'] = analysis_df['defense_tackles_won'] / analysis_df['defense_tackles'].replace(0, np.nan)
        analysis_df['pressure_regains_pct'] = analysis_df['defense_pressures_regains'] / analysis_df['defense_pressures'].replace(0, np.nan)
        
        # Calculate possession metrics
        analysis_df['pass_completion_pct'] = analysis_df['possession_passes_completed'] / analysis_df['possession_passes'].replace(0, np.nan)
        analysis_df['dribble_success_pct'] = analysis_df['possession_dribbles_completed'] / analysis_df['possession_dribbles'].replace(0, np.nan)
        
        return analysis_df
    
    def save_processed_data(self, data: pd.DataFrame, filename: str):
        """
        Save processed data to CSV
        
        Args:
            data: DataFrame to save
            filename: Name of the file (without extension)
        """
        output_dir = os.path.join(self.data_dir, 'processed')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{filename}.csv")
        data.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")
    
    def _convert_age(self, age_str: str) -> float:
        """Convert age string (e.g., '24-075') to float years"""
        if not age_str:
            return None
        try:
            years, days = map(int, age_str.split('-'))
            return years + days/365
        except:
            return None
    
    def _convert_stat(self, value: Union[str, int, float]) -> Optional[float]:
        """Convert string stat to float, handling percentages and missing values"""
        if not value or value == '-':
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # Remove commas and convert percentages
            value = str(value).replace(',', '')
            if value.endswith('%'):
                return float(value.rstrip('%')) / 100
            return float(value)
        except:
            return None

def main():
    """Main function to process all data"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
    processor = DataProcessor(data_dir)
    
    # Load data
    logger.info("Loading team and standings data...")
    team_data = processor.load_team_data()
    standings_data = processor.load_standings_data()
    
    # Process different aspects
    logger.info("Processing player statistics...")
    players_df = processor.process_player_stats(team_data)
    
    logger.info("Processing match data...")
    matches_df = processor.process_team_matches(team_data)
    
    logger.info("Processing standings data...")
    standings_df = processor.process_standings(standings_data)
    
    # Create analysis features
    logger.info("Creating analysis features...")
    analysis_df = processor.create_analysis_features(players_df, matches_df)
    
    # Save processed data
    logger.info("Saving processed data...")
    processor.save_processed_data(players_df, 'players_processed')
    processor.save_processed_data(matches_df, 'matches_processed')
    processor.save_processed_data(standings_df, 'standings_processed')
    processor.save_processed_data(analysis_df, 'analysis_features')
    
    logger.info("Data processing completed successfully!")

if __name__ == "__main__":
    main()

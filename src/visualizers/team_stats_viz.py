import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
from typing import Dict, List, Optional
import numpy as np

# Add src directory to Python path
src_dir = str(Path(__file__).resolve().parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from utils import get_logger

logger = get_logger('visualizer.team_stats')

class TeamStatsVisualizer:
    def __init__(self, stats_file: str):
        """
        Initialize the Team Stats Visualizer
        
        Args:
            stats_file (str): Path to the team stats JSON file
        """
        self.stats_file = stats_file
        self.team_data = self._load_stats()
        self.setup_style()
        
    def _load_stats(self) -> Dict:
        """Load team statistics from JSON file"""
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading team stats: {e}")
            return {}
            
    def setup_style(self):
        """Set up plotting style"""
        try:
            plt.style.use('seaborn-v0_8')  # Updated style name
            sns.set_palette("husl")
            plt.rcParams['figure.figsize'] = [12, 8]
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['axes.labelsize'] = 12
        except Exception as e:
            logger.warning(f"Could not set custom style: {e}. Using default style.")
            
    def plot_playing_time_distribution(self, save_path: Optional[str] = None):
        """Plot distribution of playing time among squad players"""
        try:
            df = pd.DataFrame(self.team_data['playing_time'])
            df['minutes_90s'] = pd.to_numeric(df['minutes_90s'], errors='coerce')
            df = df.sort_values('minutes_90s', ascending=False).head(15)
            
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x='position', y='minutes_90s')
            plt.title('Playing Time Distribution (Top 15 Players)')
            plt.xlabel('Position')
            plt.ylabel('90s Played')
            plt.xticks(rotation=45)
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting playing time distribution: {e}")
            
    def plot_goal_creation_analysis(self, save_path: Optional[str] = None):
        """Plot goal creation statistics"""
        try:
            df = pd.DataFrame(self.team_data['goal_creation'])
            df = df.sort_values('gca_per90', ascending=False).head(10)
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Goal-creating actions per 90
            sns.barplot(data=df, x='gca_per90', y=df.index, ax=ax1)
            ax1.set_title('Goal-Creating Actions per 90')
            ax1.set_xlabel('GCA per 90')
            ax1.set_ylabel('Player')
            
            # Shot-creating actions per 90
            sns.barplot(data=df, x='sca_per90', y=df.index, ax=ax2)
            ax2.set_title('Shot-Creating Actions per 90')
            ax2.set_xlabel('SCA per 90')
            ax2.set_ylabel('')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting goal creation analysis: {e}")
            
    def plot_defensive_performance(self, save_path: Optional[str] = None):
        """Plot defensive performance metrics"""
        try:
            df = pd.DataFrame(self.team_data['defense'])
            df = df[df['minutes_90s'] >= 5]  # Filter for players with significant minutes
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Tackles
            sns.scatterplot(data=df, x='tackles', y='interceptions', 
                          size='minutes_90s', hue='position', ax=axes[0, 0])
            axes[0, 0].set_title('Tackles vs Interceptions')
            
            # Blocks
            df_blocks = df.sort_values('blocks', ascending=False).head(10)
            sns.barplot(data=df_blocks, x='blocks', y=df_blocks.index, ax=axes[0, 1])
            axes[0, 1].set_title('Top 10 Players - Blocks')
            
            # Tackles by field position
            df_melted = pd.melt(df, id_vars=['position'], 
                              value_vars=['tackles_def_3rd', 'tackles_mid_3rd', 'tackles_att_3rd'])
            sns.boxplot(data=df_melted, x='position', y='value', hue='variable', ax=axes[1, 0])
            axes[1, 0].set_title('Tackles by Field Position')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # Success rates
            df['tackle_success'] = df['tackles_won'] / df['tackles'] * 100
            sns.scatterplot(data=df, x='tackle_success', y='challenge_tackles_pct',
                          size='tackles', hue='position', ax=axes[1, 1])
            axes[1, 1].set_title('Tackle Success vs Challenge Success')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting defensive performance: {e}")
            
    def plot_possession_analysis(self, save_path: Optional[str] = None):
        """Plot possession and ball progression metrics"""
        try:
            df = pd.DataFrame(self.team_data['possession'])
            df = df[df['minutes_90s'] >= 5]  # Filter for players with significant minutes
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Touches by position
            touch_cols = ['touches_def_3rd', 'touches_mid_3rd', 'touches_att_3rd']
            df_touches = df.sort_values('touches', ascending=False).head(10)
            df_touches[touch_cols].plot(kind='bar', stacked=True, ax=axes[0, 0])
            axes[0, 0].set_title('Touch Distribution by Field Position (Top 10)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Progressive carries
            sns.scatterplot(data=df, x='progressive_carries', y='carries_into_final_third',
                          size='minutes_90s', hue='position', ax=axes[0, 1])
            axes[0, 1].set_title('Progressive Carries vs Final Third Entries')
            
            # Take-on success
            df['take_on_success'] = df['take_ons_won'] / df['take_ons'] * 100
            df_take_ons = df[df['take_ons'] >= 10].sort_values('take_on_success', ascending=False)
            sns.barplot(data=df_take_ons.head(10), x='take_on_success', y=df_take_ons.head(10).index,
                       ax=axes[1, 0])
            axes[1, 0].set_title('Take-on Success Rate (Min. 10 attempts)')
            
            # Progressive passes received
            df_prog = df.sort_values('progressive_passes_received', ascending=False).head(10)
            sns.barplot(data=df_prog, x='progressive_passes_received', y=df_prog.index, ax=axes[1, 1])
            axes[1, 1].set_title('Progressive Passes Received (Top 10)')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting possession analysis: {e}")
            
    def plot_team_performance_over_time(self, save_path: Optional[str] = None):
        """Plot team performance metrics over time"""
        try:
            df = pd.DataFrame(self.team_data['matches'])
            
            # Check if required columns exist
            required_cols = ['date', 'goals_for', 'goals_against', 'xg_for', 'xg_against']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns. Available columns: {df.columns.tolist()}")
                return
                
            # Convert date and sort
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Convert numeric columns
            numeric_cols = ['goals_for', 'goals_against', 'xg_for', 'xg_against']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            fig, axes = plt.subplots(2, 1, figsize=(15, 12))
            
            # Goals scored and conceded
            axes[0].plot(df['date'], df['goals_for'], label='Goals For', marker='o')
            axes[0].plot(df['date'], df['goals_against'], label='Goals Against', marker='o')
            axes[0].set_title('Goals Scored and Conceded Over Time')
            axes[0].legend()
            axes[0].tick_params(axis='x', rotation=45)
            axes[0].grid(True)
            
            # Expected goals (xG)
            axes[1].plot(df['date'], df['xg_for'], label='xG For', marker='o')
            axes[1].plot(df['date'], df['xg_against'], label='xG Against', marker='o')
            axes[1].set_title('Expected Goals (xG) Over Time')
            axes[1].legend()
            axes[1].tick_params(axis='x', rotation=45)
            axes[1].grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            logger.error(f"Error plotting team performance over time: {e}")
            
    def generate_all_visualizations(self, output_dir: str):
        """Generate all visualizations and save them to the specified directory"""
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate all plots
            self.plot_playing_time_distribution(f"{output_dir}/playing_time.png")
            self.plot_goal_creation_analysis(f"{output_dir}/goal_creation.png")
            self.plot_defensive_performance(f"{output_dir}/defensive_performance.png")
            self.plot_possession_analysis(f"{output_dir}/possession_analysis.png")
            self.plot_team_performance_over_time(f"{output_dir}/team_performance.png")
            
            logger.info(f"All visualizations saved to {output_dir}")
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
            
if __name__ == "__main__":
    # Test the visualizer with Liverpool's stats
    stats_file = "data/teams/822bd0ba_stats_20250108.json"
    output_dir = "data/visualizations/liverpool"
    
    visualizer = TeamStatsVisualizer(stats_file)
    visualizer.generate_all_visualizations(output_dir)

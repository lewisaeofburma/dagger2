import os
import json
import shutil
from datetime import datetime, timedelta
from .logger import get_logger

logger = get_logger()

class FileManager:
    def __init__(self, base_dir=None):
        """
        Initialize FileManager
        
        Args:
            base_dir (str): Base directory for all operations. Defaults to project root.
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.base_dir = base_dir
        
        # Create necessary directories
        self.dirs = {
            'data': os.path.join(base_dir, 'data'),
            'teams': os.path.join(base_dir, 'data', 'teams'),
            'standings': os.path.join(base_dir, 'data', 'standings'),
            'stats': os.path.join(base_dir, 'data', 'stats'),
            'logs': os.path.join(base_dir, 'logs'),
            'debug': os.path.join(base_dir, 'debug')
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
    
    def save_json(self, data, filename, category):
        """
        Save data to a JSON file with backup
        
        Args:
            data: Data to save
            filename (str): Name of the file
            category (str): Category (teams, standings, or stats)
        """
        if category not in ['teams', 'standings', 'stats']:
            raise ValueError(f"Invalid category: {category}")
            
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            # Create full file path
            filepath = os.path.join(self.dirs[category], filename)
            
            # Create backup if file exists
            if os.path.exists(filepath):
                backup_dir = os.path.join(self.dirs[category], 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{os.path.splitext(filename)[0]}_{timestamp}.json"
                backup_path = os.path.join(backup_dir, backup_name)
                
                shutil.copy2(filepath, backup_path)
                logger.debug(f"Created backup at {backup_path}")
            
            # Save new data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved data to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")
            raise
    
    def load_json(self, filename, category):
        """
        Load data from a JSON file
        
        Args:
            filename (str): Name of the file
            category (str): Category (teams, standings, or stats)
            
        Returns:
            dict: Loaded data
        """
        if category not in ['teams', 'standings', 'stats']:
            raise ValueError(f"Invalid category: {category}")
            
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = os.path.join(self.dirs[category], filename)
            
            if not os.path.exists(filepath):
                logger.error(f"File not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded data from {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {e}")
            return None
    
    def cleanup_old_files(self, days=7):
        """
        Clean up old files
        
        Args:
            days (int): Delete files older than this many days
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            for category in ['teams', 'standings', 'stats']:
                backup_dir = os.path.join(self.dirs[category], 'backups')
                if not os.path.exists(backup_dir):
                    continue
                
                for filename in os.listdir(backup_dir):
                    filepath = os.path.join(backup_dir, filename)
                    if os.path.getctime(filepath) < cutoff.timestamp():
                        os.remove(filepath)
                        logger.debug(f"Deleted old file: {filepath}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
            
    def get_debug_dir(self):
        """Get the debug directory path"""
        return self.dirs['debug']

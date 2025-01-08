import os
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from .logger import get_logger

logger = get_logger()

class FileManager:
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize FileManager
        
        Args:
            base_dir: Base directory for all operations. Defaults to project root.
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.base_dir = Path(base_dir)
        
        # Create necessary directories
        self.dirs = {
            'data': self.base_dir / 'data',
            'logs': self.base_dir / 'logs',
            'debug': self.base_dir / 'debug'
        }
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_data(self, data: Dict[str, Any], filename: str, category: str) -> Optional[str]:
        """
        Save data to a JSON file in the appropriate category directory
        
        Args:
            data: Data to save
            filename: Name of the file
            category: Category of data (teams, standings, etc.)
            
        Returns:
            str: Path to saved file if successful, None otherwise
        """
        try:
            filepath = self.dirs['data'] / category / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename = filepath.name
                filepath = filepath.parent / filename
            
            # Backup existing file if it exists
            if filepath.exists():
                backup_dir = self.dirs['data'] / category / 'backups'
                backup_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d')
                backup_name = f"{filepath.stem}_{timestamp}.json"
                backup_path = backup_dir / backup_name
                
                shutil.copy2(filepath, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved data to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}", exc_info=True)
            return None
    
    def load_data(self, filename: str, category: str) -> Optional[Dict[str, Any]]:
        """
        Load data from a JSON file
        
        Args:
            filename: Name of the file
            category: Category (teams, standings, or stats)
            
        Returns:
            dict: Loaded data if successful, None otherwise
        """
        if category not in ['teams', 'standings', 'stats']:
            raise ValueError(f"Invalid category: {category}")
            
        try:
            # Ensure filename has .json extension
            if not filename.endswith('.json'):
                filename += '.json'
            
            filepath = self.dirs['data'] / category / filename
            
            if not filepath.exists():
                logger.error(f"File not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded data from {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {str(e)}")
            return None
    
    def cleanup_old_files(self, days: int = 7, categories: Optional[List[str]] = None) -> None:
        """
        Clean up old files
        
        Args:
            days: Delete files older than this many days
            categories: List of categories to clean up. If None, clean up all categories.
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            if categories is None:
                categories = ['teams', 'standings', 'stats']
            
            for category in categories:
                backup_dir = self.dirs['data'] / category / 'backups'
                if not backup_dir.exists():
                    continue
                
                for filepath in backup_dir.glob('*.json'):
                    if filepath.stat().st_ctime < cutoff.timestamp():
                        filepath.unlink()
                        logger.debug(f"Deleted old file: {filepath}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")
            
    def get_dir(self, category: str) -> Optional[str]:
        """
        Get the path to a category directory
        
        Args:
            category: Directory category
            
        Returns:
            str: Directory path if it exists, None otherwise
        """
        if category not in ['teams', 'standings', 'stats']:
            logger.error(f"Invalid category: {category}")
            return None
            
        return str(self.dirs['data'] / category)

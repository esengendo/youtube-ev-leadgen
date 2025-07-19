"""
Shared utilities module for YouTube EV Lead Generation Pipeline
Consolidates common data loading, validation, and processing functions
"""

import os
import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import hashlib
import pickle

class DataLoader:
    """Centralized data loading and caching utility"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key based on file path and modification time"""
        try:
            stat = os.stat(file_path)
            content = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.md5(content.encode()).hexdigest()
        except OSError:
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for given cache key"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def load_csv_cached(self, file_path: str, **kwargs) -> Optional[pd.DataFrame]:
        """Load CSV with caching to prevent redundant reads"""
        if not os.path.exists(file_path):
            self.logger.warning(f"File not found: {file_path}")
            return None
        
        cache_key = self._get_cache_key(file_path)
        cache_path = self._get_cache_path(cache_key)
        
        # Try to load from cache first
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    df = pickle.load(f)
                self.logger.debug(f"Loaded {file_path} from cache")
                return df
            except Exception as e:
                self.logger.warning(f"Cache read failed for {file_path}: {e}")
        
        # Load from file and cache
        try:
            df = pd.read_csv(file_path, **kwargs)
            
            # Cache the dataframe
            with open(cache_path, 'wb') as f:
                pickle.dump(df, f)
            
            self.logger.info(f"Loaded {len(df)} rows from {file_path}")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load {file_path}: {e}")
            return None
    
    def save_csv_safe(self, df: pd.DataFrame, file_path: str, backup: bool = True) -> bool:
        """Safely save CSV with backup and validation"""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create backup if file exists
            if backup and os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                os.rename(file_path, backup_path)
            
            # Save with validation
            df.to_csv(file_path, index=False)
            
            # Verify the saved file
            test_df = pd.read_csv(file_path)
            if len(test_df) != len(df):
                raise ValueError(f"Row count mismatch: expected {len(df)}, got {len(test_df)}")
            
            self.logger.info(f"Successfully saved {len(df)} rows to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save {file_path}: {e}")
            return False


class DataValidator:
    """Data validation and schema checking utilities"""
    
    @staticmethod
    def validate_comments_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate comments dataframe schema"""
        required_columns = ['Comment', 'Username', 'Timestamp']
        errors = []
        
        # Check required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check data types and content
        if 'Comment' in df.columns:
            if df['Comment'].isnull().sum() > len(df) * 0.1:  # More than 10% null
                errors.append("Too many null comments (>10%)")
        
        if 'Timestamp' in df.columns:
            try:
                pd.to_datetime(df['Timestamp'])
            except Exception:
                errors.append("Invalid timestamp format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_leads_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate leads dataframe schema"""
        required_columns = ['Username', 'ConversionProbability', 'LeadScore']
        errors = []
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Validate probability range
        if 'ConversionProbability' in df.columns:
            if not df['ConversionProbability'].between(0, 1).all():
                errors.append("ConversionProbability must be between 0 and 1")
        
        return len(errors) == 0, errors


class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        self._config_cache = {}
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration file with caching"""
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        config_path = self.config_dir / f"{config_name}.json"
        
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}")
            return {}
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self._config_cache[config_name] = config
            self.logger.debug(f"Loaded config: {config_name}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config {config_name}: {e}")
            return {}
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get standardized file paths"""
        return {
            'raw_comments': 'data/comments_data.csv',
            'clean_comments': 'data/comments_data_cleaned.csv',
            'enriched_comments': 'data/comments_data_enriched.csv',
            'qualified_leads': 'data/qualified_leads.csv',
            'predicted_leads': 'data/leads_predicted.csv',
            'objection_analysis': 'data/objection_analysis.csv',
            'model_path': 'models/lead_conversion_model.pkl',
            'alerts_log': 'reports/alerts_log.json',
            'executive_report': 'reports/executive_dashboard.txt'
        }
    
    def get_business_thresholds(self) -> Dict[str, float]:
        """Get business metric thresholds"""
        return {
            'high_conversion_threshold': 0.95,
            'negative_sentiment_spike_threshold': 0.3,
            'new_leads_alert_threshold': 10,
            'objection_spike_threshold': 0.25,
            'min_comment_length': 5,
            'max_api_retries': 3,
            'api_timeout': 30
        }


class FileUtils:
    """File system utilities with cross-platform support"""
    
    @staticmethod
    def ensure_dir(path: str) -> bool:
        """Ensure directory exists with proper error handling"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to create directory {path}: {e}")
            return False
    
    @staticmethod
    def safe_remove(file_path: str) -> bool:
        """Safely remove file if it exists"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to remove {file_path}: {e}")
            return False
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """Get file size in megabytes"""
        try:
            return os.path.getsize(file_path) / (1024 * 1024)
        except OSError:
            return 0.0


class PerformanceMonitor:
    """Simple performance monitoring utilities"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.checkpoints = {}
        self.logger = logging.getLogger(__name__)
    
    def checkpoint(self, name: str) -> float:
        """Create a performance checkpoint"""
        now = datetime.now()
        duration = (now - self.start_time).total_seconds()
        self.checkpoints[name] = duration
        self.logger.info(f"Checkpoint '{name}': {duration:.2f}s")
        return duration
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
    
    def log_performance_summary(self):
        """Log performance summary"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        memory_mb = self.get_memory_usage_mb()
        
        self.logger.info(f"Performance Summary:")
        self.logger.info(f"  Total execution time: {total_time:.2f}s")
        self.logger.info(f"  Memory usage: {memory_mb:.1f}MB")
        
        for name, duration in self.checkpoints.items():
            self.logger.info(f"  {name}: {duration:.2f}s")


# Global instances for easy access
data_loader = DataLoader()
config_manager = ConfigManager()
validator = DataValidator()
file_utils = FileUtils()
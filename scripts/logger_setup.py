"""
Centralized logging setup for YouTube EV Lead Generation Pipeline
"""

import logging
import logging.config
import json
import os
from pathlib import Path

def setup_logging(config_path: str = "config/logging_config.json", log_level: str = None):
    """
    Setup logging configuration for the entire pipeline
    
    Args:
        config_path: Path to logging configuration file
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR)
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Load logging configuration
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Override log level if provided
            if log_level:
                level = getattr(logging, log_level.upper(), logging.INFO)
                if 'loggers' in config:
                    for logger_config in config['loggers'].values():
                        logger_config['level'] = log_level.upper()
                if 'root' in config:
                    config['root']['level'] = log_level.upper()
            
            logging.config.dictConfig(config)
            
        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=logging.INFO,
                format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler('logs/pipeline.log')
                ]
            )
            logging.getLogger(__name__).error(f"Failed to load logging config: {e}")
    else:
        # Basic configuration if config file doesn't exist
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/pipeline.log')
            ]
        )
        logging.getLogger(__name__).warning(f"Logging config not found: {config_path}")

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (defaults to calling module)
    
    Returns:
        Configured logger instance
    """
    if name is None:
        # Get the calling module name
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logging.getLogger(name)

# Auto-setup logging when module is imported
setup_logging()
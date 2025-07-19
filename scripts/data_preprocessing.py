import pandas as pd
import re
import os
from utils import data_loader, config_manager, validator, file_utils
from logger_setup import get_logger

# Use centralized configuration
file_paths = config_manager.get_file_paths()
RAW_CSV = file_paths['raw_comments']
CLEAN_CSV = file_paths['clean_comments']
thresholds = config_manager.get_business_thresholds()

# Setup logging
logger = get_logger(__name__)

def clean_comment(text):
    if not isinstance(text, str):
        return ""
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)
    # Remove emojis and non-ASCII
    text = text.encode("ascii", "ignore").decode()
    # Remove special characters and numbers (keep basic punctuation)
    text = re.sub(r"[^a-zA-Z\s.,!?']", " ", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def main():
    try:
        logger.info("Starting data preprocessing pipeline")
        
        # Load data using cached loader
        df = data_loader.load_csv_cached(RAW_CSV)
        if df is None:
            logger.error(f"Failed to load raw data from {RAW_CSV}")
            return False
        
        logger.info(f"Loaded {len(df)} raw comments")
        
        # Validate input schema
        is_valid, errors = validator.validate_comments_schema(df)
        if not is_valid:
            logger.error(f"Input validation failed: {errors}")
            return False

        # Remove duplicates
        initial_count = len(df)
        df = df.drop_duplicates(subset=["Username", "Comment", "Timestamp"])
        duplicates_removed = initial_count - len(df)
        logger.info(f"Removed {duplicates_removed} duplicates")

        # Drop rows with missing essential fields
        df = df.dropna(subset=["Comment", "Username"])
        logger.info(f"After removing missing data: {len(df)} comments")

        # Clean comment text
        logger.info("Cleaning comment text...")
        df["Cleaned_Comment"] = df["Comment"].apply(clean_comment)
        
        # Remove comments that are too short or empty after cleaning
        min_length = thresholds['min_comment_length']
        df = df[df["Cleaned_Comment"].str.len() > min_length]
        logger.info(f"After removing short comments (<{min_length} chars): {len(df)} comments")

        # Add comment length for future analysis
        df["comment_length"] = df["Cleaned_Comment"].str.len()
        
        # Save cleaned data safely
        if data_loader.save_csv_safe(df, CLEAN_CSV):
            logger.info(f"Successfully saved {len(df)} cleaned comments")
            logger.debug(f"Columns: {list(df.columns)}")
            return True
        else:
            logger.error("Failed to save cleaned data")
            return False
            
    except Exception as e:
        logger.error(f"Data preprocessing failed: {e}")
        return False

if __name__ == "__main__":
    main()
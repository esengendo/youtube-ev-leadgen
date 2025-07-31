import pandas as pd
import os
import re
import torch
from transformers import pipeline
import numpy as np
from tqdm import tqdm

CLEAN_CSV = "data/comments_data_cleaned.csv"
OUTPUT_CSV = "data/comments_data_enriched.csv"

# Determine device and batch size based on system capabilities
device = 0 if torch.cuda.is_available() else -1
batch_size = 32 if torch.cuda.is_available() else 16

# Load sentiment analysis pipeline with GPU support and batching
sentiment_analyzer = pipeline(
    "sentiment-analysis", 
    model="distilbert-base-uncased-finetuned-sst-2-english",
    device=device,
    batch_size=batch_size,
    return_all_scores=False
)

# Vectorized intent detection for batch processing
def detect_intent_vectorized(comments_series):
    """Vectorized intent detection using pandas string operations"""
    comments_lower = comments_series.str.lower()
    
    # Purchase Intent - highest priority
    purchase_pattern = r'\b(?:buy|purchase|test drive|own|order|reserve|book|get one|get this|interested in buying)\b'
    purchase_mask = comments_lower.str.contains(purchase_pattern, regex=True, na=False)
    
    # Inquiry/Interest 
    inquiry_pattern = r'\b(?:how much|price|cost|range|feature|spec|availability|when|where|details|info|information|question)\b'
    inquiry_mask = comments_lower.str.contains(inquiry_pattern, regex=True, na=False) | comments_series.str.contains('\?', na=False)
    
    # Competitor Mention
    competitor_pattern = r'\b(?:tesla|ford|chevy|hyundai|kia|volkswagen|bmw|mercedes|audi)\b'
    competitor_mask = comments_lower.str.contains(competitor_pattern, regex=True, na=False)
    
    # Assign intents based on priority (Purchase > Inquiry > Competitor > General)
    intents = pd.Series("General Comment", index=comments_series.index)
    intents[competitor_mask] = "Competitor Mention"
    intents[inquiry_mask] = "Interest/Inquiry"
    intents[purchase_mask] = "Purchase Intent"
    
    return intents

def process_sentiment_batch(comments_batch):
    """Process sentiment analysis in batches with error handling"""
    try:
        # Convert to list and filter out empty/null comments
        comments_list = [str(comment) for comment in comments_batch if pd.notna(comment) and str(comment).strip()]
        
        if not comments_list:
            return ["NEUTRAL"] * len(comments_batch)
        
        # Process batch through sentiment analyzer
        results = sentiment_analyzer(comments_list)
        
        # Extract labels and map back to original batch size
        sentiments = []
        result_idx = 0
        
        for comment in comments_batch:
            if pd.notna(comment) and str(comment).strip():
                sentiments.append(results[result_idx]['label'])
                result_idx += 1
            else:
                sentiments.append("NEUTRAL")
        
        return sentiments
        
    except Exception as e:
        print(f"Batch processing failed, falling back to individual processing: {e}")
        # Fallback to individual processing
        return [sentiment_analyzer(str(comment))[0]['label'] if pd.notna(comment) else "NEUTRAL" for comment in comments_batch]

def main():
    if not os.path.exists(CLEAN_CSV):
        print(f"Cleaned data file not found: {CLEAN_CSV}")
        return
    
    print("Loading cleaned data...")
    df = pd.read_csv(CLEAN_CSV)
    if df.empty:
        print("No data to process.")
        return
    
    print(f"Processing {len(df)} comments with optimized batch processing...")
    
    # Vectorized intent detection (instant for all comments)
    print("Applying vectorized intent detection...")
    df["Intent"] = detect_intent_vectorized(df["Cleaned_Comment"])
    
    # Batch sentiment analysis with progress bar
    print("Running optimized sentiment analysis...")
    comments = df["Cleaned_Comment"].fillna("").astype(str).tolist()
    
    # Process in optimized batches
    all_sentiments = []
    for i in tqdm(range(0, len(comments), batch_size), desc="Processing sentiment batches"):
        batch = comments[i:i + batch_size]
        batch_sentiments = process_sentiment_batch(batch)
        all_sentiments.extend(batch_sentiments)
    
    df["Sentiment"] = all_sentiments
    
    # Save enriched data
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Optimized processing complete! Enriched data saved to {OUTPUT_CSV}")
    print(f"📊 Processed {len(df)} comments with GPU acceleration: {'✅' if torch.cuda.is_available() else '❌'}")
    
    # Print performance summary
    intent_counts = df["Intent"].value_counts()
    sentiment_counts = df["Sentiment"].value_counts()
    print(f"\n📈 Results Summary:")
    print(f"Intent Distribution: {dict(intent_counts)}")
    print(f"Sentiment Distribution: {dict(sentiment_counts)}")

if __name__ == "__main__":
    main()

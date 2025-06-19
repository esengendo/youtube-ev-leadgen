import pandas as pd
import os
import re
from transformers import pipeline

CLEAN_CSV = "data/comments_data_cleaned.csv"
OUTPUT_CSV = "data/comments_data_enriched.csv"

# Load sentiment analysis pipeline (HuggingFace Transformers)
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Business rules for intent detection
def detect_intent(comment):
    comment = comment.lower()
    # Purchase Intent
    purchase_keywords = [
        "buy", "purchase", "test drive", "own", "order", "reserve", "book", "get one", "get this", "interested in buying"
    ]
    if any(kw in comment for kw in purchase_keywords):
        return "Purchase Intent"
    # Inquiry/Interest
    inquiry_keywords = [
        "how much", "price", "cost", "range", "feature", "spec", "availability", "when", "where", "details", "info", "information", "question"
    ]
    if any(kw in comment for kw in inquiry_keywords) or '?' in comment:
        return "Interest/Inquiry"
    # Competitor Mention
    competitors = ["tesla", "ford", "chevy", "hyundai", "kia", "volkswagen", "bmw", "mercedes", "audi"]
    if any(brand in comment for brand in competitors):
        return "Competitor Mention"
    # General Positive/Negative/Other
    return "General Comment"

def main():
    if not os.path.exists(CLEAN_CSV):
        print(f"Cleaned data file not found: {CLEAN_CSV}")
        return
    df = pd.read_csv(CLEAN_CSV)
    if df.empty:
        print("No data to process.")
        return

    # Sentiment analysis
    print("Running sentiment analysis (this may take a few minutes)...")
    df["Sentiment"] = df["Cleaned_Comment"].astype(str).apply(lambda x: sentiment_analyzer(x)[0]["label"])

    # Intent detection
    print("Applying business rules for intent detection...")
    df["Intent"] = df["Cleaned_Comment"].astype(str).apply(detect_intent)

    # Save enriched data
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Enriched data with sentiment and intent saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

import pandas as pd
import re
import os

RAW_CSV = "data/comments_data.csv"
CLEAN_CSV = "data/comments_data_cleaned.csv"

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
    if not os.path.exists(RAW_CSV):
        print(f"Raw data file not found: {RAW_CSV}")
        return

    df = pd.read_csv(RAW_CSV)
    print(f"Loaded {len(df)} raw comments")

    # Remove duplicates
    initial_count = len(df)
    df = df.drop_duplicates(subset=["Username", "Comment", "Timestamp"])
    print(f"Removed {initial_count - len(df)} duplicates")

    # Drop rows with missing essential fields
    df = df.dropna(subset=["Comment", "Username"])
    print(f"After removing missing data: {len(df)} comments")

    # Clean comment text
    df["Cleaned_Comment"] = df["Comment"].apply(clean_comment)

    # Remove comments that are too short or empty after cleaning
    df = df[df["Cleaned_Comment"].str.len() > 5]
    print(f"After removing short comments: {len(df)} comments")

    # Add comment length for future analysis
    df["comment_length"] = df["Cleaned_Comment"].str.len()

    # Save cleaned data
    os.makedirs("data", exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False)
    print(f"Cleaned data saved to {CLEAN_CSV}")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    main()
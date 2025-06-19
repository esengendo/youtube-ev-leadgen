import pandas as pd
import re
import os
import plotly.express as px

RAW_CSV = "data/comments_data.csv"
CLEAN_CSV = "data/comments_data_cleaned.csv"

def clean_comment(text):
    if not isinstance(text, str):
        return ""
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r"http\\S+|www\\.\\S+", "", text)
    # Remove emojis and non-ASCII
    text = text.encode("ascii", "ignore").decode()
    # Remove special characters and numbers (keep basic punctuation)
    text = re.sub(r"[^a-zA-Z\\s.,!?']", " ", text)
    # Remove extra whitespace
    text = re.sub(r"\\s+", " ", text).strip()
    return text

def main():
    if not os.path.exists(RAW_CSV):
        print(f"Raw data file not found: {RAW_CSV}")
        return

    df = pd.read_csv(RAW_CSV)

    # Remove duplicates
    df = df.drop_duplicates(subset=["Username", "Comment", "Timestamp"])

    # Drop rows with missing essential fields
    df = df.dropna(subset=["Comment", "Username"])

    # Clean comment text
    df["Cleaned_Comment"] = df["Comment"].apply(clean_comment)

    # Remove comments that are too short or empty after cleaning
    df = df[df["Cleaned_Comment"].str.len() > 5]

    # Save cleaned data
    os.makedirs("data", exist_ok=True)
    df.to_csv(CLEAN_CSV, index=False)
    print(f"Cleaned data saved to {CLEAN_CSV}")

    fig = px.line(
        df.groupby(['date', 'Sentiment']).size().reset_index(name='num_comments'),
        x='date', y='num_comments', color='Sentiment',
        title='Comments Over Time by Sentiment'
    )
    fig.show()

    fig = px.histogram(
        df, x='comment_length', color='Intent', barmode='overlay',
        nbins=30, title='Comment Length Distribution by Intent'
    )
    fig.show()

    fig = px.pie(
        df, names='Intent', title='Distribution of Comment Intents'
    )
    fig.show()

    top_users = df['Username'].value_counts().head(10).index
    fig = px.bar(
        df[df['Username'].isin(top_users)].groupby(['Username', 'Sentiment']).size().reset_index(name='count'),
        x='Username', y='count', color='Sentiment',
        title='Top 10 Users by Sentiment'
    )
    fig.show()

if __name__ == "__main__":
    main()
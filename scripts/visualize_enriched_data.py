import pandas as pd
import plotly.express as px
import os

ENRICHED_CSV = "data/comments_data_enriched.csv"
IMG_DIR = "visualizations"

def load_data():
    if not os.path.exists(ENRICHED_CSV):
        print(f"Enriched data file not found: {ENRICHED_CSV}")
        return None
    return pd.read_csv(ENRICHED_CSV)

def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    df = load_data()
    if df is None or df.empty:
        print("No data to visualize.")
        return

    print(f"Total comments: {len(df)}")
    print("Sample rows:")
    print(df.head())

    # 1. Sentiment Distribution
    fig1 = px.histogram(df, x='Sentiment', color='Sentiment', title='Sentiment Distribution')
    fig1.write_html(f"{IMG_DIR}/sentiment_distribution.html")
    fig1.show()

    # 2. Intent Distribution
    fig2 = px.histogram(df, x='Intent', color='Intent', title='Intent Distribution')
    fig2.write_html(f"{IMG_DIR}/intent_distribution.html")
    fig2.show()

    # 3. Sentiment Over Time
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df = df.dropna(subset=['Timestamp'])
        df['date'] = df['Timestamp'].dt.date
        sentiment_time = df.groupby(['date', 'Sentiment']).size().reset_index(name='num_comments')
        fig3 = px.line(sentiment_time, x='date', y='num_comments', color='Sentiment', title='Sentiment Over Time')
        fig3.write_html(f"{IMG_DIR}/sentiment_over_time.html")
        fig3.show()

    # 4. Intent Over Time
    if 'Timestamp' in df.columns:
        intent_time = df.groupby(['date', 'Intent']).size().reset_index(name='num_comments')
        fig4 = px.line(intent_time, x='date', y='num_comments', color='Intent', title='Intent Over Time')
        fig4.write_html(f"{IMG_DIR}/intent_over_time.html")
        fig4.show()

    # 5. Sentiment by Intent (Stacked Bar)
    fig5 = px.histogram(df, x='Intent', color='Sentiment', barmode='stack', title='Sentiment by Intent')
    fig5.write_html(f"{IMG_DIR}/sentiment_by_intent.html")
    fig5.show()

    print(f"\n[INFO] All sentiment and intent visualizations saved as HTML in the '{IMG_DIR}' directory.")
    print("[INFO] Open the HTML files in your browser to view and export PNGs using the camera icon.")

if __name__ == "__main__":
    main()

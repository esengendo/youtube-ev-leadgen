import pandas as pd
import plotly.express as px
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt

CLEAN_CSV = "data/comments_data_cleaned.csv"
IMG_DIR = "visualizations"

def load_data():
    if not os.path.exists(CLEAN_CSV):
        print(f"Cleaned data file not found: {CLEAN_CSV}")
        return None
    return pd.read_csv(CLEAN_CSV)

def plot_wordcloud(texts, title, save_path=None):
    text = " ".join(texts)
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(title)
    if save_path:
        plt.savefig(save_path, bbox_inches='tight')
    plt.show()
    plt.close()

def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    df = load_data()
    if df is None or df.empty:
        print("No data to visualize.")
        return

    print(f"Total comments: {len(df)}")
    print("Sample rows:")
    print(df.head())

    # 1. Top 10 Most Active Users
    user_counts = df['Username'].value_counts().head(10)
    fig1 = px.bar(user_counts, title='Top 10 Most Active Users', labels={'index': 'Username', 'value': 'Number of Comments'})
    fig1.write_html(f"{IMG_DIR}/top_10_users.html")
    fig1.show()

    # 2. Comment Length Distribution
    df['comment_length'] = df['Cleaned_Comment'].str.len()
    fig2 = px.histogram(df, x='comment_length', nbins=30, title='Comment Length Distribution')
    fig2.write_html(f"{IMG_DIR}/comment_length_distribution.html")
    fig2.show()

    # 3. Comments Over Time
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df = df.dropna(subset=['Timestamp'])
        df['date'] = df['Timestamp'].dt.date
        date_counts = df.groupby('date').size().reset_index(name='num_comments')
        fig3 = px.line(date_counts, x='date', y='num_comments', title='Comments Over Time')
        fig3.write_html(f"{IMG_DIR}/comments_over_time.html")
        fig3.show()

    # 4. Word Cloud of Most Common Words
    plot_wordcloud(df['Cleaned_Comment'], 'Most Common Words in Comments', save_path=f"{IMG_DIR}/wordcloud.png")

    # 5. Comments by Hour of Day (Engagement Pattern)
    if 'Timestamp' in df.columns:
        df['hour'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.hour
        hour_counts = df.groupby('hour').size().reset_index(name='num_comments')
        fig5 = px.bar(hour_counts, x='hour', y='num_comments', title='Comments by Hour of Day', labels={'hour': 'Hour of Day', 'num_comments': 'Number of Comments'})
        fig5.write_html(f"{IMG_DIR}/comments_by_hour.html")
        fig5.show()

    # 6. Pie Chart: Top 5 Users vs Others
    top5 = user_counts.head(5)
    others = user_counts[5:].sum()
    pie_data = pd.concat([top5, pd.Series({'Others': others})])
    fig6 = px.pie(pie_data, values=pie_data.values, names=pie_data.index, title='Top 5 Users vs Others')
    fig6.write_html(f"{IMG_DIR}/top5_vs_others_pie.html")
    fig6.show()

    print(f"\n[INFO] All visualizations saved as HTML (and word cloud as PNG) in the '{IMG_DIR}' directory.")
    print("[INFO] Open the HTML files in your browser to view and export PNGs using the camera icon.")

if __name__ == "__main__":
    main()

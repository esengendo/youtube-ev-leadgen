import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.title("YouTube EV Lead Generation Dashboard")

ENRICHED_CSV = "../data/comments_data_enriched.csv"
LEADS_CSV = "../data/leads.csv"
ALERTS_TXT = "../reports/alerts_summary.txt"

# Load data
df = pd.read_csv(ENRICHED_CSV) if os.path.exists(ENRICHED_CSV) else None
leads = pd.read_csv(LEADS_CSV) if os.path.exists(LEADS_CSV) else None

if df is not None:
    st.header("Sentiment & Intent Trends")
    df['date'] = pd.to_datetime(df['Timestamp'], errors='coerce').dt.date
    sentiment_time = df.groupby(['date', 'Sentiment']).size().reset_index(name='num_comments')
    fig1 = px.line(sentiment_time, x='date', y='num_comments', color='Sentiment', title='Sentiment Over Time')
    st.plotly_chart(fig1)

    intent_time = df.groupby(['date', 'Intent']).size().reset_index(name='num_comments')
    fig2 = px.line(intent_time, x='date', y='num_comments', color='Intent', title='Intent Over Time')
    st.plotly_chart(fig2)

    st.header("Top Influencers & Advocates")
    influencer_counts = df['Username'].value_counts().head(5)
    st.write("**Top 5 Influencers:**")
    st.write(influencer_counts)
    advocates = df[df['Sentiment'] == 'POSITIVE']['Username'].value_counts().head(5)
    st.write("**Top 5 Advocates:**")
    st.write(advocates)

if leads is not None:
    st.header("Lead List (Top 10 by Score)")
    st.dataframe(leads.sort_values(by='LeadScore', ascending=False).head(10))

if os.path.exists(ALERTS_TXT):
    st.header("Automated Alerts")
    with open(ALERTS_TXT) as f:
        st.text(f.read())

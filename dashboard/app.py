import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="EV Lead Generation Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success-card {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Data loading functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_leads_data():
    """Load leads data with caching"""
    if os.path.exists("data/leads_predicted.csv"):
        return pd.read_csv("data/leads_predicted.csv")
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_sentiment_data():
    """Load sentiment data with caching"""
    if os.path.exists("data/comments_data_enriched.csv"):
        df = pd.read_csv("data/comments_data_enriched.csv")
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_qualified_leads():
    """Load qualified leads data"""
    if os.path.exists("data/qualified_leads.csv"):
        return pd.read_csv("data/qualified_leads.csv")
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_objection_data():
    """Load objection data with caching"""
    if os.path.exists("data/objection_analysis.csv"):
        return pd.read_csv("data/objection_analysis.csv")
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_alerts_data():
    """Load alerts data with caching"""
    if os.path.exists("reports/alerts_log.json"):
        with open("reports/alerts_log.json", 'r') as f:
            return json.load(f)
    return {"alerts": [], "historical_metrics": []}

def load_executive_dashboard():
    """Load executive dashboard text"""
    if os.path.exists("reports/executive_dashboard.txt"):
        with open("reports/executive_dashboard.txt", 'r') as f:
            return f.read()
    return None

def load_leads_summary():
    """Load leads summary text"""
    if os.path.exists("reports/leads_summary.txt"):
        with open("reports/leads_summary.txt", 'r') as f:
            return f.read()
    return None

def create_kpi_metrics(leads_df):
    """Create KPI metrics for the dashboard"""
    if leads_df.empty:
        return {}
    
    return {
        "total_leads": len(leads_df),
        "high_prob_leads": len(leads_df[leads_df['ConversionProbability'] >= 0.95]),
        "avg_conversion_prob": leads_df['ConversionProbability'].mean(),
        "hot_leads": len(leads_df[leads_df['LeadQuality'] == 'Hot Lead']),
        "warm_leads": len(leads_df[leads_df['LeadQuality'] == 'Warm Lead']),
        "purchase_intent": len(leads_df[leads_df['Intent'] == 'Purchase Intent']),
        "avg_lead_score": leads_df['LeadScore'].mean(),
        "revenue_potential": len(leads_df[leads_df['ConversionProbability'] >= 0.95]) * 45000
    }

def create_conversion_funnel(leads_df):
    """Create conversion funnel visualization"""
    if leads_df.empty:
        return go.Figure()
    
    funnel_data = [
        ("Total Leads", len(leads_df)),
        ("High Intent (80%+)", len(leads_df[leads_df['ConversionProbability'] >= 0.8])),
        ("Very High Intent (90%+)", len(leads_df[leads_df['ConversionProbability'] >= 0.9])),
        ("Ultra High Intent (95%+)", len(leads_df[leads_df['ConversionProbability'] >= 0.95])),
        ("Certain Conversion (99%+)", len(leads_df[leads_df['ConversionProbability'] >= 0.99]))
    ]
    
    fig = go.Figure(go.Funnel(
        y=[item[0] for item in funnel_data],
        x=[item[1] for item in funnel_data],
        textinfo="value+percent initial",
        marker=dict(color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"])
    ))
    
    fig.update_layout(
        title="Lead Conversion Funnel",
        font=dict(size=14),
        height=400
    )
    
    return fig

def create_lead_quality_pie(leads_df):
    """Create lead quality distribution pie chart"""
    if leads_df.empty:
        return go.Figure()
    
    quality_counts = leads_df['LeadQuality'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=quality_counts.index,
        values=quality_counts.values,
        hole=0.4,
        marker_colors=['#ff6b6b', '#4ecdc4']
    )])
    
    fig.update_layout(
        title="Lead Quality Distribution",
        font=dict(size=14),
        height=400
    )
    
    return fig

def create_sentiment_timeline(sentiment_df):
    """Create sentiment timeline"""
    if sentiment_df.empty:
        return go.Figure()
    
    # Group by date and sentiment
    sentiment_df['date'] = sentiment_df['Timestamp'].dt.date
    daily_sentiment = sentiment_df.groupby(['date', 'Sentiment']).size().reset_index(name='count')
    
    fig = px.line(daily_sentiment, x='date', y='count', color='Sentiment',
                  title="Sentiment Trends Over Time",
                  labels={'count': 'Number of Comments', 'date': 'Date'})
    
    fig.update_layout(height=400)
    return fig

def create_intent_analysis(sentiment_df):
    """Create intent analysis chart"""
    if sentiment_df.empty:
        return go.Figure()
    
    intent_counts = sentiment_df['Intent'].value_counts()
    
    fig = go.Figure(data=[go.Bar(
        x=intent_counts.index,
        y=intent_counts.values,
        marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    )])
    
    fig.update_layout(
        title="Intent Distribution",
        xaxis_title="Intent Type",
        yaxis_title="Number of Comments",
        height=400
    )
    
    return fig

def display_html_visualization(file_path, title):
    """Display HTML visualization if it exists"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            html_content = f.read()
        st.markdown(f"### {title}")
        st.components.v1.html(html_content, height=500, scrolling=True)
        return True
    return False

# Main Dashboard
def main():
    # Header
    st.markdown('<h1 class="main-header">🚗 EV Lead Generation Intelligence Platform</h1>', 
                unsafe_allow_html=True)
    st.markdown("### 🚀 Comprehensive Business Analytics Dashboard")
    
    # Load all data
    leads_df = load_leads_data()
    sentiment_df = load_sentiment_data()
    qualified_df = load_qualified_leads()
    objection_df = load_objection_data()
    alerts_data = load_alerts_data()
    executive_summary = load_executive_dashboard()
    leads_summary = load_leads_summary()
    
    # Check if we have data
    has_data = not leads_df.empty or not sentiment_df.empty
    
    if not has_data:
        st.markdown('<div class="alert-medium">', unsafe_allow_html=True)
        st.info("🔧 **Dashboard Ready!** No data files found. Run the data pipeline to populate the dashboard.")
        st.markdown("""
        **To generate data:**
        1. Mount data volume: `docker run -v ./youtube-ev-leadgen/data:/app/data -p 8501:8501 esengendo730/youtube-ev-leadgen`
        2. Run pipeline: `docker exec <container> python scripts/run_pipeline.py`
        3. Refresh this dashboard
        
        **Available features when data is loaded:**
        - 📊 Executive KPI Dashboard
        - 🎯 Lead Conversion Analytics
        - 📈 Sentiment & Intent Trends
        - 🚨 Automated Business Alerts
        - 💰 Revenue Potential Analysis
        - 🔍 Customer Objection Insights
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Success message
    st.markdown('<div class="success-card">', unsafe_allow_html=True)
    st.success("✅ Data loaded successfully! Displaying comprehensive analytics.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # KPI Dashboard
    if not leads_df.empty:
        kpis = create_kpi_metrics(leads_df)
        
        st.markdown("## 📊 Executive KPI Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Leads", f"{kpis.get('total_leads', 0):,}")
            st.metric("Hot Leads", f"{kpis.get('hot_leads', 0):,}")
            
        with col2:
            st.metric("High-Probability Leads", f"{kpis.get('high_prob_leads', 0):,}")
            st.metric("Warm Leads", f"{kpis.get('warm_leads', 0):,}")
            
        with col3:
            st.metric("Avg Conversion Probability", f"{kpis.get('avg_conversion_prob', 0):.1%}")
            st.metric("Purchase Intent Leads", f"{kpis.get('purchase_intent', 0):,}")
            
        with col4:
            st.metric("Revenue Potential", f"${kpis.get('revenue_potential', 0):,}")
            st.metric("Avg Lead Score", f"{kpis.get('avg_lead_score', 0):.1f}/10")
    
    # Charts Section
    st.markdown("## 📈 Lead Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not leads_df.empty:
            funnel_fig = create_conversion_funnel(leads_df)
            st.plotly_chart(funnel_fig, use_container_width=True)
    
    with col2:
        if not leads_df.empty:
            pie_fig = create_lead_quality_pie(leads_df)
            st.plotly_chart(pie_fig, use_container_width=True)
    
    # Sentiment & Intent Analysis
    st.markdown("## 💭 Sentiment & Intent Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not sentiment_df.empty:
            sentiment_fig = create_sentiment_timeline(sentiment_df)
            st.plotly_chart(sentiment_fig, use_container_width=True)
    
    with col2:
        if not sentiment_df.empty:
            intent_fig = create_intent_analysis(sentiment_df)
            st.plotly_chart(intent_fig, use_container_width=True)
    
    # Lead Tables
    st.markdown("## 🎯 Top Performing Leads")
    
    if not leads_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔥 Highest Conversion Probability")
            top_conversion = leads_df.nlargest(10, 'ConversionProbability')[['Username', 'Comment', 'ConversionProbability', 'LeadQuality']]
            st.dataframe(top_conversion, use_container_width=True)
        
        with col2:
            st.markdown("### ⭐ Highest Lead Scores")
            top_scores = leads_df.nlargest(10, 'LeadScore')[['Username', 'Comment', 'LeadScore', 'LeadQuality']]
            st.dataframe(top_scores, use_container_width=True)
    
    # Business Intelligence Visualizations
    st.markdown("## 📊 Advanced Analytics Visualizations")
    
    viz_files = [
        ("visualizations/conversion_probability_distribution.html", "Conversion Probability Distribution"),
        ("visualizations/sentiment_over_time.html", "Sentiment Trends Analysis"),
        ("visualizations/intent_over_time.html", "Intent Trends Analysis"),
        ("visualizations/roc_curve.html", "Model Performance (ROC Curve)"),
        ("visualizations/feature_importances.html", "Feature Importance Analysis"),
        ("visualizations/leadscore_vs_probability.html", "Lead Score vs Conversion Probability")
    ]
    
    viz_displayed = 0
    for file_path, title in viz_files:
        if display_html_visualization(file_path, title):
            viz_displayed += 1
            if viz_displayed >= 3:  # Limit to avoid overwhelming the dashboard
                break
    
    # Executive Summary
    if executive_summary:
        st.markdown("## 📋 Executive Summary")
        st.text(executive_summary)
    
    # Alerts Section
    if alerts_data.get("alerts"):
        st.markdown("## 🚨 Business Alerts")
        for alert in alerts_data["alerts"][-5:]:  # Show last 5 alerts
            alert_type = alert.get("type", "info")
            if alert_type == "high":
                st.markdown(f'<div class="alert-high">🔴 <strong>High Priority:</strong> {alert.get("message", "")}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-medium">🟡 <strong>Medium Priority:</strong> {alert.get("message", "")}</div>', 
                           unsafe_allow_html=True)
    
    # Top Influencers Section
    if not sentiment_df.empty:
        st.markdown("## 👥 Community Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌟 Top Influencers")
            influencers = sentiment_df['Username'].value_counts().head(10)
            st.bar_chart(influencers)
        
        with col2:
            st.markdown("### 💚 Top Advocates (Positive Sentiment)")
            advocates = sentiment_df[sentiment_df['Sentiment'] == 'POSITIVE']['Username'].value_counts().head(10)
            st.bar_chart(advocates)

if __name__ == "__main__":
    main()
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
    daily_sentiment = sentiment_df.groupby([
        sentiment_df['Timestamp'].dt.date, 'Sentiment'
    ]).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    colors = {'POSITIVE': '#2ca02c', 'NEGATIVE': '#d62728', 'NEUTRAL': '#ff7f0e'}
    
    for sentiment in daily_sentiment.columns:
        fig.add_trace(go.Scatter(
            x=daily_sentiment.index,
            y=daily_sentiment[sentiment],
            mode='lines+markers',
            name=sentiment,
            line=dict(color=colors.get(sentiment, '#1f77b4'))
        ))
    
    fig.update_layout(
        title="Daily Sentiment Trends",
        xaxis_title="Date",
        yaxis_title="Number of Comments",
        height=400
    )
    
    return fig

def create_objection_analysis(objection_df):
    """Create objection analysis chart"""
    if objection_df.empty:
        return go.Figure()
    
    # Parse objections and count them
    objection_counts = {}
    for _, row in objection_df.iterrows():
        try:
            objections = eval(row['objections']) if pd.notna(row['objections']) and row['objections'] != '[]' else []
            for obj in objections:
                objection_counts[obj] = objection_counts.get(obj, 0) + 1
        except:
            continue
    
    if not objection_counts:
        return go.Figure()
    
    # Get top 10 objections
    top_objections = dict(sorted(objection_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    fig = go.Figure(data=[go.Bar(
        x=list(top_objections.values()),
        y=list(top_objections.keys()),
        orientation='h',
        marker_color='#ff6b6b'
    )])
    
    fig.update_layout(
        title="Top Customer Objections",
        xaxis_title="Frequency",
        height=400
    )
    
    return fig

def display_alerts(alerts_data):
    """Display active alerts"""
    alerts = alerts_data.get("alerts", [])
    
    if not alerts:
        st.success("✅ No active alerts - All metrics within normal ranges")
        return
    
    # Get recent alerts (last 24 hours)
    recent_alerts = []
    for alert in alerts:
        try:
            alert_time = datetime.fromisoformat(str(alert['timestamp']).replace('Z', '+00:00'))
            if datetime.now().replace(tzinfo=alert_time.tzinfo) - alert_time < timedelta(days=1):
                recent_alerts.append(alert)
        except:
            recent_alerts.append(alert)  # Include if timestamp parsing fails
    
    if not recent_alerts:
        st.info("ℹ️ No recent alerts (last 24 hours)")
        return
    
    st.subheader(f"🚨 Active Alerts ({len(recent_alerts)})")
    
    for alert in recent_alerts[-5:]:  # Show last 5 alerts
        priority = alert.get('priority', 'MEDIUM')
        message = alert.get('message', 'No message')
        action = alert.get('action', 'No action specified')
        
        if priority == 'HIGH':
            st.markdown(f"""
            <div class="alert-high">
                <strong>🔴 HIGH PRIORITY:</strong> {message}<br>
                <strong>Action:</strong> {action}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-medium">
                <strong>🟡 MEDIUM PRIORITY:</strong> {message}<br>
                <strong>Action:</strong> {action}
            </div>
            """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🚗 EV Lead Generation Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    leads_df = load_leads_data()
    sentiment_df = load_sentiment_data()
    objection_df = load_objection_data()
    alerts_data = load_alerts_data()
    
    if leads_df.empty:
        st.error("❌ No lead data found. Please run the lead generation pipeline first.")
        return
    
    # Sidebar filters
    st.sidebar.header("📊 Dashboard Filters")
    
    # Lead quality filter
    quality_options = ['All'] + list(leads_df['LeadQuality'].unique())
    selected_quality = st.sidebar.selectbox("Lead Quality", quality_options)
    
    # Conversion probability filter
    min_prob = st.sidebar.slider("Minimum Conversion Probability", 0.0, 1.0, 0.0, 0.05)
    
    # Intent filter
    intent_options = ['All'] + list(leads_df['Intent'].unique())
    selected_intent = st.sidebar.selectbox("Intent Type", intent_options)
    
    # Apply filters
    filtered_df = leads_df.copy()
    if selected_quality != 'All':
        filtered_df = filtered_df[filtered_df['LeadQuality'] == selected_quality]
    if selected_intent != 'All':
        filtered_df = filtered_df[filtered_df['Intent'] == selected_intent]
    filtered_df = filtered_df[filtered_df['ConversionProbability'] >= min_prob]
    
    # KPI Metrics
    kpis = create_kpi_metrics(filtered_df)
    
    st.subheader("📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Qualified Leads",
            value=f"{kpis.get('total_leads', 0):,}",
            delta=f"+{kpis.get('total_leads', 0) - len(leads_df) + len(filtered_df)}"
        )
    
    with col2:
        st.metric(
            label="High-Probability Leads (95%+)",
            value=f"{kpis.get('high_prob_leads', 0):,}",
            delta=f"{kpis.get('high_prob_leads', 0) / max(kpis.get('total_leads', 1), 1) * 100:.1f}%"
        )
    
    with col3:
        st.metric(
            label="Average Conversion Probability",
            value=f"{kpis.get('avg_conversion_prob', 0):.1%}",
            delta=f"Score: {kpis.get('avg_lead_score', 0):.1f}/10"
        )
    
    with col4:
        st.metric(
            label="Revenue Potential",
            value=f"${kpis.get('revenue_potential', 0):,}",
            delta="High-prob leads × $45K"
        )
    
    # Alerts Section
    display_alerts(alerts_data)
    
    # Charts Section
    st.subheader("📊 Analytics Dashboard")
    
    # Row 1: Funnel and Quality Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        funnel_fig = create_conversion_funnel(filtered_df)
        st.plotly_chart(funnel_fig, use_container_width=True)
    
    with col2:
        quality_fig = create_lead_quality_pie(filtered_df)
        st.plotly_chart(quality_fig, use_container_width=True)
    
    # Row 2: Sentiment Timeline and Objection Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        if not sentiment_df.empty:
            sentiment_fig = create_sentiment_timeline(sentiment_df)
            st.plotly_chart(sentiment_fig, use_container_width=True)
        else:
            st.info("No sentiment data available")
    
    with col2:
        if not objection_df.empty:
            objection_fig = create_objection_analysis(objection_df)
            st.plotly_chart(objection_fig, use_container_width=True)
        else:
            st.info("No objection data available")
    
    # Lead Details Table
    st.subheader("🎯 Top Leads Details")
    
    # Show top 20 leads by conversion probability
    top_leads = filtered_df.nlargest(20, 'ConversionProbability')[
        ['Username', 'ConversionProbability', 'LeadQuality', 'Intent', 'LeadScore', 'Sentiment']
    ]
    
    # Format the table
    top_leads['ConversionProbability'] = top_leads['ConversionProbability'].apply(lambda x: f"{x:.1%}")
    top_leads['LeadScore'] = top_leads['LeadScore'].apply(lambda x: f"{x:.1f}")
    
    st.dataframe(
        top_leads,
        use_container_width=True,
        hide_index=True
    )
    
    # Export functionality
    st.subheader("📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Filtered Leads"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"filtered_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📈 Export Executive Report"):
            if os.path.exists("reports/executive_dashboard.txt"):
                with open("reports/executive_dashboard.txt", 'r') as f:
                    report = f.read()
                st.download_button(
                    label="Download Report",
                    data=report,
                    file_name=f"executive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    with col3:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"**Total Records:** {len(leads_df):,} | "
        f"**Filtered Records:** {len(filtered_df):,}"
    )

if __name__ == "__main__":
    main() 
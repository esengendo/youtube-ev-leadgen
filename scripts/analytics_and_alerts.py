import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File paths
LEADS_PREDICTED_CSV = "data/leads_predicted.csv"
OBJECTION_CSV = "data/objection_analysis.csv"
ENRICHED_CSV = "data/comments_data_enriched.csv"
ALERTS_LOG = "reports/alerts_log.json"
EXECUTIVE_REPORT = "reports/executive_dashboard.txt"

# Business thresholds
HIGH_CONVERSION_THRESHOLD = 0.95
NEGATIVE_SENTIMENT_SPIKE_THRESHOLD = 0.3
NEW_LEADS_ALERT_THRESHOLD = 10
OBJECTION_SPIKE_THRESHOLD = 0.25

def load_historical_data():
    """Load historical metrics for comparison"""
    if os.path.exists(ALERTS_LOG):
        with open(ALERTS_LOG, 'r') as f:
            return json.load(f)
    return {"historical_metrics": [], "alerts": []}

def save_alert_data(data):
    """Save alert data for historical tracking"""
    os.makedirs("reports", exist_ok=True)
    with open(ALERTS_LOG, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def analyze_lead_performance():
    """Comprehensive lead performance analysis"""
    if not os.path.exists(LEADS_PREDICTED_CSV):
        return None
    
    df = pd.read_csv(LEADS_PREDICTED_CSV)
    
    metrics = {
        "timestamp": datetime.now(),
        "total_leads": len(df),
        "high_probability_leads": len(df[df['ConversionProbability'] >= HIGH_CONVERSION_THRESHOLD]),
        "avg_conversion_probability": df['ConversionProbability'].mean(),
        "hot_leads": len(df[df['LeadQuality'] == 'Hot Lead']),
        "warm_leads": len(df[df['LeadQuality'] == 'Warm Lead']),
        "purchase_intent_leads": len(df[df['Intent'] == 'Purchase Intent']),
        "avg_lead_score": df['LeadScore'].mean(),
        "top_conversion_prob": df['ConversionProbability'].max(),
        "conversion_rate_estimate": (df['ConversionProbability'] >= 0.8).sum() / len(df) * 100
    }
    
    return metrics

def analyze_sentiment_trends():
    """Analyze sentiment trends and detect spikes"""
    if not os.path.exists(ENRICHED_CSV):
        return None
    
    df = pd.read_csv(ENRICHED_CSV)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Recent sentiment analysis (last 7 days)
    recent_date = df['Timestamp'].max() - timedelta(days=7)
    recent_df = df[df['Timestamp'] >= recent_date]
    
    sentiment_metrics = {
        "total_comments": len(df),
        "recent_comments": len(recent_df),
        "negative_sentiment_rate": (df['Sentiment'] == 'NEGATIVE').sum() / len(df),
        "recent_negative_rate": (recent_df['Sentiment'] == 'NEGATIVE').sum() / len(recent_df) if len(recent_df) > 0 else 0,
        "positive_sentiment_rate": (df['Sentiment'] == 'POSITIVE').sum() / len(df),
        "neutral_sentiment_rate": (df['Sentiment'] == 'NEUTRAL').sum() / len(df)
    }
    
    return sentiment_metrics

def analyze_objection_patterns():
    """Analyze objection patterns and identify trends"""
    if not os.path.exists(OBJECTION_CSV):
        return None
    
    df = pd.read_csv(OBJECTION_CSV)
    
    # Parse objections (assuming they're stored as string representations of lists)
    objection_counts = {}
    for _, row in df.iterrows():
        try:
            objections = eval(row['objections']) if pd.notna(row['objections']) and row['objections'] != '[]' else []
            for obj in objections:
                objection_counts[obj] = objection_counts.get(obj, 0) + 1
        except:
            continue
    
    total_comments_with_objections = sum(1 for _, row in df.iterrows() 
                                       if pd.notna(row['objections']) and row['objections'] != '[]')
    
    objection_metrics = {
        "total_comments_analyzed": len(df),
        "comments_with_objections": total_comments_with_objections,
        "objection_rate": total_comments_with_objections / len(df) if len(df) > 0 else 0,
        "top_objections": dict(sorted(objection_counts.items(), key=lambda x: x[1], reverse=True)[:5])
    }
    
    return objection_metrics

def generate_alerts(current_metrics, historical_data):
    """Generate business-critical alerts"""
    alerts = []
    
    # High-value lead alert
    if current_metrics['lead_metrics']['high_probability_leads'] >= NEW_LEADS_ALERT_THRESHOLD:
        alerts.append({
            "type": "HIGH_VALUE_LEADS",
            "priority": "HIGH",
            "message": f"🔥 {current_metrics['lead_metrics']['high_probability_leads']} high-probability leads (95%+) identified!",
            "action": "Immediate sales team notification recommended",
            "timestamp": datetime.now()
        })
    
    # Conversion rate alert
    if current_metrics['lead_metrics']['conversion_rate_estimate'] > 25:
        alerts.append({
            "type": "HIGH_CONVERSION_RATE",
            "priority": "MEDIUM",
            "message": f"📈 Exceptional conversion rate: {current_metrics['lead_metrics']['conversion_rate_estimate']:.1f}%",
            "action": "Scale marketing efforts on successful channels",
            "timestamp": datetime.now()
        })
    
    # Negative sentiment spike alert
    if current_metrics['sentiment_metrics'] and current_metrics['sentiment_metrics']['recent_negative_rate'] > NEGATIVE_SENTIMENT_SPIKE_THRESHOLD:
        alerts.append({
            "type": "NEGATIVE_SENTIMENT_SPIKE",
            "priority": "HIGH",
            "message": f"⚠️ Negative sentiment spike: {current_metrics['sentiment_metrics']['recent_negative_rate']:.1%}",
            "action": "Review recent product/service issues and customer support",
            "timestamp": datetime.now()
        })
    
    # Objection pattern alert
    if current_metrics['objection_metrics'] and current_metrics['objection_metrics']['objection_rate'] > OBJECTION_SPIKE_THRESHOLD:
        alerts.append({
            "type": "HIGH_OBJECTION_RATE",
            "priority": "MEDIUM",
            "message": f"🚨 High objection rate: {current_metrics['objection_metrics']['objection_rate']:.1%}",
            "action": f"Address top objections: {list(current_metrics['objection_metrics']['top_objections'].keys())[:3]}",
            "timestamp": datetime.now()
        })
    
    return alerts

def generate_executive_report(metrics, alerts):
    """Generate executive-level business report"""
    report = f"""
==========================================================
EXECUTIVE DASHBOARD - EV LEAD GENERATION ANALYTICS
==========================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 KEY BUSINESS METRICS
==========================================================
Total Qualified Leads: {metrics['lead_metrics']['total_leads']:,}
High-Probability Leads (95%+): {metrics['lead_metrics']['high_probability_leads']:,}
Estimated Conversion Rate: {metrics['lead_metrics']['conversion_rate_estimate']:.1f}%
Average Lead Score: {metrics['lead_metrics']['avg_lead_score']:.1f}/10

🎯 LEAD QUALITY BREAKDOWN
==========================================================
Hot Leads (Immediate Action): {metrics['lead_metrics']['hot_leads']:,}
Warm Leads (Nurturing): {metrics['lead_metrics']['warm_leads']:,}
Purchase Intent Leads: {metrics['lead_metrics']['purchase_intent_leads']:,}
Top Conversion Probability: {metrics['lead_metrics']['top_conversion_prob']:.1%}

📈 SENTIMENT ANALYSIS
==========================================================
Total Comments Analyzed: {metrics['sentiment_metrics']['total_comments']:,}
Positive Sentiment Rate: {metrics['sentiment_metrics']['positive_sentiment_rate']:.1%}
Negative Sentiment Rate: {metrics['sentiment_metrics']['negative_sentiment_rate']:.1%}
Recent Negative Trend: {metrics['sentiment_metrics']['recent_negative_rate']:.1%}

🚨 OBJECTION INTELLIGENCE
==========================================================
Comments with Objections: {metrics['objection_metrics']['comments_with_objections']:,}
Objection Rate: {metrics['objection_metrics']['objection_rate']:.1%}
Top Customer Concerns: {', '.join(list(metrics['objection_metrics']['top_objections'].keys())[:3])}

⚡ ACTIVE ALERTS ({len(alerts)})
==========================================================
"""
    
    for alert in alerts:
        priority_emoji = "🔴" if alert['priority'] == 'HIGH' else "🟡"
        report += f"{priority_emoji} {alert['type']}: {alert['message']}\n"
        report += f"   Action: {alert['action']}\n\n"
    
    if not alerts:
        report += "✅ No active alerts - All metrics within normal ranges\n"
    
    report += f"""
💰 BUSINESS IMPACT ESTIMATE
==========================================================
Potential Revenue Pipeline: {metrics['lead_metrics']['high_probability_leads'] * 45000:,} USD
(Based on {metrics['lead_metrics']['high_probability_leads']} high-prob leads × $45K avg EV price)

Monthly Lead Value: {metrics['lead_metrics']['total_leads'] * 2500:,} USD
(Based on {metrics['lead_metrics']['total_leads']} leads × $2.5K avg lead value)

==========================================================
"""
    
    return report

def send_executive_alert(report, alerts):
    """Send executive alert email (if configured)"""
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    executive_email = os.getenv('EXECUTIVE_EMAIL', 'executive@company.com')
    
    if not email_user or not email_password:
        print("Email credentials not configured. Skipping email alert.")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = executive_email
        msg['Subject'] = f"EV Lead Generation Alert - {len(alerts)} Active Alerts"
        
        msg.attach(MIMEText(report, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, executive_email, text)
        server.quit()
        
        print(f"Executive alert sent to {executive_email}")
    except Exception as e:
        print(f"Failed to send email alert: {e}")

def main():
    print("🚀 Running Professional Lead Generation Analytics & Alerts...")
    
    # Analyze current performance
    lead_metrics = analyze_lead_performance()
    sentiment_metrics = analyze_sentiment_trends()
    objection_metrics = analyze_objection_patterns()
    
    if not lead_metrics:
        print("❌ No lead data found. Run lead generation pipeline first.")
        return
    
    current_metrics = {
        "lead_metrics": lead_metrics,
        "sentiment_metrics": sentiment_metrics,
        "objection_metrics": objection_metrics
    }
    
    # Load historical data and generate alerts
    historical_data = load_historical_data()
    alerts = generate_alerts(current_metrics, historical_data)
    
    # Generate executive report
    executive_report = generate_executive_report(current_metrics, alerts)
    
    # Save reports
    os.makedirs("reports", exist_ok=True)
    with open(EXECUTIVE_REPORT, 'w') as f:
        f.write(executive_report)
    
    # Update historical data
    historical_data["historical_metrics"].append(current_metrics)
    historical_data["alerts"].extend(alerts)
    save_alert_data(historical_data)
    
    # Print summary
    print(f"✅ Analysis complete:")
    print(f"   📊 {lead_metrics['total_leads']} leads analyzed")
    print(f"   🔥 {lead_metrics['high_probability_leads']} high-probability leads identified")
    print(f"   ⚡ {len(alerts)} active alerts generated")
    print(f"   📄 Executive report saved to {EXECUTIVE_REPORT}")
    
    # Send alerts if high priority
    high_priority_alerts = [a for a in alerts if a['priority'] == 'HIGH']
    if high_priority_alerts:
        print(f"🚨 {len(high_priority_alerts)} HIGH PRIORITY alerts detected!")
        send_executive_alert(executive_report, alerts)
    
    # Display key alerts
    for alert in alerts[:3]:  # Show top 3 alerts
        priority_emoji = "🔴" if alert['priority'] == 'HIGH' else "🟡"
        print(f"{priority_emoji} {alert['message']}")

if __name__ == "__main__":
    main()

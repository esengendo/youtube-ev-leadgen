import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import joblib

LEADS_PREDICTED_CSV = "data/leads_predicted.csv"
MODEL_PATH = "models/lead_conversion_model.pkl"
IMG_DIR = "visualizations"

def main():
    if not os.path.exists(LEADS_PREDICTED_CSV):
        print("No predicted leads data found.")
        return
    
    df = pd.read_csv(LEADS_PREDICTED_CSV)
    os.makedirs(IMG_DIR, exist_ok=True)

    print(f"Total predicted leads: {len(df)}")
    print("Sample rows:")
    print(df.head())

    # 1. Conversion Probability Distribution
    fig1 = px.histogram(df, x='ConversionProbability', nbins=20, title='Conversion Probability Distribution')
    fig1.write_html(f"{IMG_DIR}/conversion_probability_distribution.html")
    fig1.show()

    # 2. Top 10 Leads Table
    print("\nTop 10 Predicted Leads:")
    top_leads = df.nlargest(10, 'ConversionProbability')[['Username', 'Comment', 'ConversionProbability', 'LeadScore', 'Intent', 'Sentiment']]
    print(top_leads)

    # 3. Feature Importance (if model available)
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            if hasattr(model, 'feature_importances_'):
                features = ['LeadScore', 'comment_length', 'is_purchase_intent', 'is_interest_inquiry', 'is_positive', 'user_comment_count']
                importances = model.feature_importances_
                fig2 = go.Figure([go.Bar(x=features, y=importances)])
                fig2.update_layout(title="Feature Importances for Lead Conversion Prediction", yaxis_title="Importance")
                fig2.write_html(f"{IMG_DIR}/feature_importances.html")
                fig2.show()
            else:
                print("Model doesn't have feature_importances_ attribute")
        except Exception as e:
            print(f"Error loading model for feature importance: {e}")

    # 4. Conversion Probability by Intent
    if 'Intent' in df.columns:
        fig3 = px.box(df, x='Intent', y='ConversionProbability', title='Conversion Probability by Intent')
        fig3.write_html(f"{IMG_DIR}/conversion_probability_by_intent.html")
        fig3.show()

    # 5. Conversion Probability by Sentiment
    if 'Sentiment' in df.columns:
        fig4 = px.box(df, x='Sentiment', y='ConversionProbability', title='Conversion Probability by Sentiment')
        fig4.write_html(f"{IMG_DIR}/conversion_probability_by_sentiment.html")
        fig4.show()

    # 6. Lead Score vs Conversion Probability Scatter
    if 'LeadScore' in df.columns:
        fig5 = px.scatter(df, x='LeadScore', y='ConversionProbability', 
                         color='Intent' if 'Intent' in df.columns else None,
                         title='Lead Score vs Conversion Probability')
        fig5.write_html(f"{IMG_DIR}/leadscore_vs_probability.html")
        fig5.show()

    # 7. High Probability Leads (95%+) Summary
    high_prob_leads = df[df['ConversionProbability'] >= 0.95]
    print(f"\nHigh-Probability Leads (95%+): {len(high_prob_leads)}")
    if len(high_prob_leads) > 0:
        print("Top High-Probability Leads:")
        print(high_prob_leads[['Username', 'ConversionProbability', 'LeadScore', 'Intent']].head())

    print(f"\n[INFO] All predicted leads visualizations saved as HTML in the '{IMG_DIR}' directory.")
    print("[INFO] Open the HTML files in your browser to view and export PNGs using the camera icon.")

if __name__ == "__main__":
    main()
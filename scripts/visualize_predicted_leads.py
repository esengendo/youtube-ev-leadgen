import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import joblib
import json
from transformers import pipeline
from dotenv import load_dotenv
import torch
from collections import Counter

LEADS_PREDICTED_CSV = "data/leads_predicted.csv"
MODEL_PATH = "models/lead_conversion_model.pkl"
IMG_DIR = "visualizations"

# Load environment variables
load_dotenv(dotenv_path='../config/.env')

# Configurable paths
DATA_PATH = os.getenv('ENRICHED_COMMENTS_PATH', '../data/enriched_comments.csv')
OBJECTION_CONFIG_PATH = os.getenv('OBJECTION_KEYWORDS_PATH', '../config/objection_keywords.json')
OUTPUT_PATH = os.getenv('OBJECTION_OUTPUT_PATH', '../data/objection_analysis.csv')

def main():
    if not os.path.exists(LEADS_PREDICTED_CSV):
        print("No predicted leads data found.")
        return
    df = pd.read_csv(LEADS_PREDICTED_CSV)
    os.makedirs(IMG_DIR, exist_ok=True)

    # 1. Conversion Probability Distribution
    fig1 = px.histogram(df, x='ConversionProbability', nbins=20, title='Conversion Probability Distribution')
    fig1.write_html(f"{IMG_DIR}/conversion_probability_distribution.html")
    fig1.show()

    # 2. Top 10 Leads Table
    print("Top 10 Predicted Leads:")
    print(df[['Username', 'Comment', 'ConversionProbability', 'LeadScore', 'Intent', 'Sentiment']].head(10))

    # 3. Feature Importance (if model available)
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        features = ['LeadScore', 'comment_length', 'is_purchase_intent', 'is_interest_inquiry', 'is_positive', 'user_comment_count']
        importances = model.feature_importances_
        fig2 = go.Figure([go.Bar(x=features, y=importances)])
        fig2.update_layout(title="Feature Importances for Lead Conversion Prediction", yaxis_title="Importance")
        fig2.write_html(f"{IMG_DIR}/feature_importances.html")
        fig2.show()

    # 4. Conversion Probability by Intent
    fig3 = px.box(df, x='Intent', y='ConversionProbability', title='Conversion Probability by Intent')
    fig3.write_html(f"{IMG_DIR}/conversion_probability_by_intent.html")
    fig3.show()

    # 5. (Optional) Actual vs. Predicted if 'Converted' column exists
    if 'Converted' in df.columns:
        from sklearn.metrics import confusion_matrix, roc_curve, auc
        import numpy as np
        y_true = df['Converted']
        y_pred = (df['ConversionProbability'] > 0.5).astype(int)
        cm = confusion_matrix(y_true, y_pred)
        print("Confusion Matrix:")
        print(cm)
        fpr, tpr, _ = roc_curve(y_true, df['ConversionProbability'])
        roc_auc = auc(fpr, tpr)
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name='ROC Curve'))
        fig4.add_trace(go.Scatter(x=[0,1], y=[0,1], mode='lines', name='Random', line=dict(dash='dash')))
        fig4.update_layout(title=f"ROC Curve (AUC={roc_auc:.2f})", xaxis_title="False Positive Rate", yaxis_title="True Positive Rate")
        fig4.write_html(f"{IMG_DIR}/roc_curve.html")
        fig4.show()

    # 1. Load data
    df = pd.read_csv(DATA_PATH)

    # 2. Load objection keywords (business-aligned, e.g., price, charging, range, etc.)
    with open(OBJECTION_CONFIG_PATH, 'r') as f:
        objection_keywords = json.load(f)  # { "price": ["expensive", "cost", ...], ... }

    # 3. Keyword-based objection detection
    def detect_keyword_objections(text, keyword_dict):
        objections = []
        text_lower = text.lower()
        for obj, keywords in keyword_dict.items():
            if any(kw in text_lower for kw in keywords):
                objections.append(obj)
        return objections

    df['objection_keywords'] = df['comment_text'].apply(lambda x: detect_keyword_objections(str(x), objection_keywords))

    # 4. Transformer-based objection detection (zero-shot classification)
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",  # Or another suitable model
        device=0 if torch.cuda.is_available() else -1
    )

    # Define candidate objection labels (business-aligned)
    candidate_labels = list(objection_keywords.keys())

    def detect_transformer_objections(text, labels, threshold=0.4):
        result = classifier(str(text), labels)
        objections = [label for label, score in zip(result['labels'], result['scores']) if score >= threshold]
        return objections

    df['objection_transformer'] = df['comment_text'].apply(lambda x: detect_transformer_objections(x, candidate_labels))

    # 5. Combine and deduplicate objections
    def combine_objections(row):
        return list(set(row['objection_keywords']) | set(row['objection_transformer']))

    df['objections'] = df.apply(combine_objections, axis=1)

    # 6. Save results
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Objection analysis complete. Results saved to {OUTPUT_PATH}")

    # 7. (Optional) Aggregate and visualize objection trends
    try:
        all_objections = [obj for sublist in df['objections'] for obj in sublist]
        objection_counts = Counter(all_objections)
        fig = px.bar(
            x=list(objection_counts.keys()),
            y=list(objection_counts.values()),
            labels={'x': 'Objection/Barrier', 'y': 'Count'},
            title='Top Objections/Barriers in YouTube Comments'
        )
        fig.write_html('../visualizations/objection_trends.html')
        print("Objection trends visualization saved to ../visualizations/objection_trends.html")
    except Exception as e:
        print(f"Visualization skipped: {e}")

if __name__ == "__main__":
    main()
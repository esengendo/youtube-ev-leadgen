import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib
from datetime import datetime

ENRICHED_CSV = "data/comments_data_enriched.csv"
LEADS_CSV = "data/leads.csv"
PREDICTED_LEADS_CSV = "data/leads_predicted.csv"
MODEL_PATH = "models/lead_conversion_model.pkl"

def derive_conversion_indicators(df):
    """
    Derive conversion likelihood from real behavioral signals in our YouTube data
    instead of using simulated labels
    """
    # Initialize conversion score
    conversion_score = np.zeros(len(df))
    
    # Ensure Comment column exists and handle NaN values
    if 'Comment' not in df.columns:
        print("Warning: No 'Comment' column found. Using empty conversion scores.")
        return np.zeros(len(df)), conversion_score
    
    # Fill NaN comments with empty strings
    df['Comment'] = df['Comment'].fillna('')
    
    # 1. Strong Purchase Intent Signals (highest weight)
    purchase_keywords = ['buy', 'purchase', 'order', 'reserve', 'reservation', 'buying', 'bought', 'ordered']
    strong_intent = df['Comment'].str.lower().str.contains('|'.join(purchase_keywords), na=False)
    conversion_score += strong_intent * 3
    
    # 2. Timeline/Urgency Indicators
    timeline_keywords = ['soon', 'next month', 'this year', '2024', '2025', 'waiting', 'delivery']
    has_timeline = df['Comment'].str.lower().str.contains('|'.join(timeline_keywords), na=False)
    conversion_score += has_timeline * 2
    
    # 3. Specific Model Interest
    model_keywords = ['r1t', 'r1s', 'r2', 'r3', 'rivian truck', 'rivian suv']
    specific_model = df['Comment'].str.lower().str.contains('|'.join(model_keywords), na=False)
    conversion_score += specific_model * 1.5
    
    # 4. Financial Readiness Signals
    financial_keywords = ['afford', 'financing', 'lease', 'payment', 'price', 'cost', 'budget']
    financial_discussion = df['Comment'].str.lower().str.contains('|'.join(financial_keywords), na=False)
    conversion_score += financial_discussion * 1
    
    # 5. High Engagement (multiple comments, long comments)
    user_comment_counts = df['Username'].value_counts()
    high_engagement = df['Username'].map(user_comment_counts) >= 2
    conversion_score += high_engagement * 1
    
    # 6. Detailed/Thoughtful Comments (length proxy for engagement)
    comment_lengths = df['Comment'].astype(str).str.len()
    long_comments = (comment_lengths > 100)
    conversion_score += long_comments * 0.5
    
    # 7. Positive Sentiment with Purchase Intent
    if 'Sentiment' in df.columns and 'Intent' in df.columns:
        positive_purchase = (df['Sentiment'] == 'POSITIVE') & (df['Intent'] == 'Purchase Intent')
        conversion_score += positive_purchase * 2
    
    # 8. Questions about Practical Details (shows serious consideration)
    practical_keywords = ['delivery', 'warranty', 'service', 'charging', 'range', 'features', 'options']
    practical_questions = df['Comment'].str.lower().str.contains('|'.join(practical_keywords), na=False)
    conversion_score += practical_questions * 1
    
    # Convert to binary labels using threshold (top 30% as likely converters)
    # Handle edge case where all scores are the same
    if conversion_score.std() == 0:
        # If all scores are identical, use median split
        threshold = conversion_score.median()
        conversion_labels = (conversion_score > threshold).astype(int)
    else:
        threshold = np.percentile(conversion_score, 70)
        conversion_labels = (conversion_score >= threshold).astype(int)
    
    return conversion_labels, conversion_score

def main():
    if not os.path.exists(LEADS_CSV):
        print(f"Leads data file not found: {LEADS_CSV}")
        return
    
    df = pd.read_csv(LEADS_CSV)
    if df.empty:
        print("No leads to process.")
        return

    print(f"Processing {len(df)} leads with real behavioral conversion indicators...")
    
    # Use real behavioral indicators instead of simulated data
    conversion_labels, conversion_scores = derive_conversion_indicators(df)
    df['Converted'] = conversion_labels
    df['ConversionScore'] = conversion_scores
    
    print(f"Identified {conversion_labels.sum()} high-probability converters from behavioral signals")

    # Feature engineering based on real data (avoid duplicates)
    df['comment_length'] = df['Comment'].fillna('').astype(str).str.len()
    df['is_purchase_intent'] = (df['Intent'] == 'Purchase Intent').astype(int) if 'Intent' in df.columns else 0
    df['is_interest_inquiry'] = (df['Intent'] == 'Interest/Inquiry').astype(int) if 'Intent' in df.columns else 0
    df['is_positive'] = (df['Sentiment'] == 'POSITIVE').astype(int) if 'Sentiment' in df.columns else 0
    
    # User engagement metrics
    user_comment_counts = df['Username'].value_counts().to_dict()
    df['user_comment_count'] = df['Username'].map(user_comment_counts)
    
    # Advanced behavioral features
    df['has_purchase_keywords'] = df['Comment'].fillna('').str.lower().str.contains(
        'buy|purchase|order|reserve|buying|bought|ordered', na=False
    ).astype(int)
    
    df['has_timeline_urgency'] = df['Comment'].fillna('').str.lower().str.contains(
        'soon|next month|this year|2024|2025|waiting|delivery', na=False
    ).astype(int)
    
    df['discusses_financials'] = df['Comment'].fillna('').str.lower().str.contains(
        'afford|financing|lease|payment|price|cost|budget', na=False
    ).astype(int)

    # Features for ML model
    features = [
        'LeadScore', 'comment_length', 'is_purchase_intent', 'is_interest_inquiry', 
        'is_positive', 'user_comment_count', 'has_purchase_keywords', 
        'has_timeline_urgency', 'discusses_financials'
    ]
    
    # Ensure all features exist
    for feature in features:
        if feature not in df.columns:
            print(f"Warning: Feature '{feature}' not found. Setting to 0.")
            df[feature] = 0
    
    X = df[features]
    y = df['Converted']

    # Only split if we have enough positive cases
    if y.sum() < 5:
        print("Warning: Very few positive conversion cases. Using all data for training.")
        X_train, X_test, y_train, y_test = X, X, y, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    # Train model
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    clf.fit(X_train, y_train)
    
    # Predictions
    y_proba = clf.predict_proba(X)[:, 1]
    
    # Save model
    os.makedirs("models", exist_ok=True)
    joblib.dump(clf, MODEL_PATH)

    # Add prediction probabilities to leads
    df['ConversionProbability'] = y_proba
    df = df.sort_values(by='ConversionProbability', ascending=False)
    df.to_csv(PREDICTED_LEADS_CSV, index=False)

    # Model performance
    if len(X_test) > 0 and y_test.sum() > 0 and len(X_test) != len(X_train):
        y_pred = clf.predict(X_test)
        print("\nModel Performance (Real Behavioral Data):")
        print(classification_report(y_test, y_pred))
        try:
            auc_score = roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])
            print(f"ROC AUC: {auc_score:.2f}")
        except:
            print("ROC AUC: Could not calculate (insufficient positive cases in test set)")
    else:
        print("\nModel trained on all data (no test split due to small dataset)")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': clf.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\nTop Conversion Predictors:")
    for _, row in feature_importance.head(5).iterrows():
        print(f"  {row['feature']}: {row['importance']:.3f}")
    
    print(f"\nPredicted leads with real behavioral conversion probabilities saved to {PREDICTED_LEADS_CSV}")
    print(f"Top 10 leads have conversion probabilities: {df['ConversionProbability'].head(10).values}")

if __name__ == "__main__":
    main()

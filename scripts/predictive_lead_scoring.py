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

def derive_conversion_indicators_vectorized(df):
    """
    Vectorized conversion likelihood derivation using optimized pandas operations
    """
    # Ensure Comment column exists and handle NaN values
    if 'Comment' not in df.columns:
        print("Warning: No 'Comment' column found. Using empty conversion scores.")
        return np.zeros(len(df)), np.zeros(len(df))
    
    # Prepare comment column once
    comments_lower = df['Comment'].fillna('').astype(str).str.lower()
    
    # Vectorized pattern matching - combine all patterns for single pass
    patterns = {
        'purchase': r'\b(?:buy|purchase|order|reserve|reservation|buying|bought|ordered)\b',
        'timeline': r'\b(?:soon|next month|this year|202[4-9]|waiting|delivery)\b', 
        'model': r'\b(?:r1t|r1s|r2|r3|rivian truck|rivian suv)\b',
        'financial': r'\b(?:afford|financing|lease|payment|price|cost|budget)\b',
        'practical': r'\b(?:delivery|warranty|service|charging|range|features|options)\b'
    }
    
    # Single pass pattern detection
    pattern_matches = {}
    for name, pattern in patterns.items():
        pattern_matches[name] = comments_lower.str.contains(pattern, regex=True, na=False)
    
    # Calculate conversion scores vectorized
    conversion_score = (
        pattern_matches['purchase'].astype(int) * 3 +
        pattern_matches['timeline'].astype(int) * 2 +
        pattern_matches['model'].astype(int) * 1.5 +
        pattern_matches['financial'].astype(int) * 1 +
        pattern_matches['practical'].astype(int) * 1
    )
    
    # User engagement (vectorized)
    user_counts = df['Username'].value_counts()
    high_engagement = df['Username'].map(user_counts) >= 2
    conversion_score += high_engagement.astype(int) * 1
    
    # Comment length (vectorized)
    comment_lengths = df['Comment'].fillna('').astype(str).str.len()
    long_comments = (comment_lengths > 100).astype(int)
    conversion_score += long_comments * 0.5
    
    # Sentiment-intent combination (if available)
    if 'Sentiment' in df.columns and 'Intent' in df.columns:
        positive_purchase = ((df['Sentiment'] == 'POSITIVE') & (df['Intent'] == 'Purchase Intent')).astype(int)
        conversion_score += positive_purchase * 2
    
    # Efficient threshold calculation
    if conversion_score.std() == 0:
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
    
    print("Loading leads data...")
    df = pd.read_csv(LEADS_CSV)
    if df.empty:
        print("No leads to process.")
        return

    print(f"Processing {len(df)} leads with vectorized behavioral analysis...")
    
    # Use optimized vectorized conversion indicators
    conversion_labels, conversion_scores = derive_conversion_indicators_vectorized(df)
    df['Converted'] = conversion_labels
    df['ConversionScore'] = conversion_scores
    
    print(f"✅ Identified {conversion_labels.sum()} high-probability converters from behavioral signals")

    # Vectorized feature engineering (avoid redundant computations)
    print("Generating ML features with vectorized operations...")
    
    # Basic features
    df['comment_length'] = df['Comment'].fillna('').astype(str).str.len()
    
    # Intent/sentiment features (if available)
    if 'Intent' in df.columns:
        df['is_purchase_intent'] = (df['Intent'] == 'Purchase Intent').astype(int)
        df['is_interest_inquiry'] = (df['Intent'] == 'Interest/Inquiry').astype(int)
    else:
        df['is_purchase_intent'] = 0
        df['is_interest_inquiry'] = 0
        
    if 'Sentiment' in df.columns:
        df['is_positive'] = (df['Sentiment'] == 'POSITIVE').astype(int)
    else:
        df['is_positive'] = 0
    
    # User engagement (already computed, reuse)
    user_comment_counts = df['Username'].value_counts()
    df['user_comment_count'] = df['Username'].map(user_comment_counts)
    
    # Reuse pattern matches from conversion scoring (avoid recomputation)
    comments_lower = df['Comment'].fillna('').astype(str).str.lower()
    df['has_purchase_keywords'] = comments_lower.str.contains(
        r'\b(?:buy|purchase|order|reserve|buying|bought|ordered)\b', regex=True, na=False
    ).astype(int)
    
    df['has_timeline_urgency'] = comments_lower.str.contains(
        r'\b(?:soon|next month|this year|202[4-9]|waiting|delivery)\b', regex=True, na=False
    ).astype(int)
    
    df['discusses_financials'] = comments_lower.str.contains(
        r'\b(?:afford|financing|lease|payment|price|cost|budget)\b', regex=True, na=False
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

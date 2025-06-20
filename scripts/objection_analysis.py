import os
import json
import pandas as pd
import torch
from transformers import pipeline
from dotenv import load_dotenv

def detect_keyword_objections(text, keyword_dict):
    objections = []
    text_lower = text.lower()
    for obj, keywords in keyword_dict.items():
        if any(kw in text_lower for kw in keywords):
            objections.append(obj)
    return objections

def detect_transformer_objections(text, labels, threshold=0.4):
    result = classifier(str(text), labels)
    objections = [label for label, score in zip(result['labels'], result['scores']) if score >= threshold]
    return objections

def combine_objections(row):
    return list(set(row['objection_keywords']) | set(row['objection_transformer']))

def main():
    # Load environment variables - use relative path that works in both environments
    load_dotenv(dotenv_path='config/.env')

    # Use relative paths that work in both local and Docker environments
    OBJECTION_CONFIG_PATH = os.getenv('OBJECTION_KEYWORDS_PATH', 'config/objection_keywords.json')
    DATA_PATH = os.getenv('ENRICHED_COMMENTS_PATH', 'data/comments_data_enriched.csv')
    OUTPUT_PATH = os.getenv('OBJECTION_OUTPUT_PATH', 'data/objection_analysis.csv')

    print("Script started")

    # 1. Load data
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded data columns: {list(df.columns)}")

    COMMENT_COL = os.getenv('COMMENT_TEXT_COL', 'Cleaned_Comment')
    print(f"Using comment text column: '{COMMENT_COL}'")
    if COMMENT_COL not in df.columns:
        print(f"ERROR: Expected comment text column '{COMMENT_COL}' not found in the data. Available columns: {list(df.columns)}")
        exit(1)

    # 2. Load objection keywords
    with open(OBJECTION_CONFIG_PATH, 'r') as f:
        objection_keywords = json.load(f)

    # 3. Keyword-based objection detection
    df['objection_keywords'] = df[COMMENT_COL].apply(lambda x: detect_keyword_objections(str(x), objection_keywords))

    # 4. Transformer-based objection detection (zero-shot classification)
    global classifier  # So detect_transformer_objections can use it
    classifier = pipeline(
        "zero-shot-classification",
        model="valhalla/distilbart-mnli-12-1",
        device=0 if torch.cuda.is_available() else -1
    )
    candidate_labels = list(objection_keywords.keys())
    df['objection_transformer'] = df[COMMENT_COL].apply(lambda x: detect_transformer_objections(x, candidate_labels))

    # 5. Combine and deduplicate objections
    df['objections'] = df.apply(combine_objections, axis=1)

    # 6. Save results
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Objection analysis complete. Results saved to {OUTPUT_PATH}")

    # 7. (Optional) Aggregate and visualize objection trends
    try:
        import plotly.express as px
        from collections import Counter

        all_objections = [obj for sublist in df['objections'] for obj in sublist]
        objection_counts = Counter(all_objections)
        fig = px.bar(
            x=list(objection_counts.keys()),
            y=list(objection_counts.values()),
            labels={'x': 'Objection/Barrier', 'y': 'Count'},
            title='Top Objections/Barriers in YouTube Comments'
        )
        fig.write_html('visualizations/objection_trends.html')
        print("Objection trends visualization saved to visualizations/objection_trends.html")
    except Exception as e:
        print(f"Visualization skipped: {e}")

if __name__ == "__main__":
    main()
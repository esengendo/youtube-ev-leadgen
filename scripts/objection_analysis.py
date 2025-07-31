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

def detect_transformer_objections_batch(texts, labels, classifier, threshold=0.4, batch_size=None):
    """Optimized batch processing with adaptive batch sizing and GPU utilization"""
    if not texts:
        return []
    
    # Adaptive batch sizing based on GPU availability and memory
    if batch_size is None:
        if torch.cuda.is_available():
            batch_size = min(32, len(texts))  # Larger batches for GPU
        else:
            batch_size = min(16, len(texts))  # Smaller batches for CPU
    
    all_objections = []
    from tqdm import tqdm
    
    for i in tqdm(range(0, len(texts), batch_size), desc="Processing objection batches"):
        batch_texts = texts[i:i + batch_size]
        try:
            # Process entire batch at once
            results = classifier(batch_texts, labels, batch_size=len(batch_texts))
            
            # Handle single text vs batch results
            if not isinstance(results, list):
                results = [results]
            
            # Extract objections for each text in batch
            for result in results:
                if isinstance(result, dict) and 'scores' in result:
                    objections = [label for label, score in zip(result['labels'], result['scores']) if score >= threshold]
                else:
                    objections = []
                all_objections.append(objections)
                
        except Exception as e:
            print(f"Batch processing failed for batch {i//batch_size + 1}, using fallback: {e}")
            # Efficient fallback processing
            batch_objections = []
            for text in batch_texts:
                try:
                    single_result = classifier(str(text), labels)
                    if isinstance(single_result, dict):
                        objections = [label for label, score in zip(single_result['labels'], single_result['scores']) if score >= threshold]
                    else:
                        objections = []
                    batch_objections.append(objections)
                except Exception as fallback_error:
                    print(f"Individual processing also failed: {fallback_error}")
                    batch_objections.append([])
            all_objections.extend(batch_objections)
    
    return all_objections

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

    # 3. Keyword-based objection detection and initialize transformer column
    df['objection_keywords'] = df[COMMENT_COL].apply(lambda x: detect_keyword_objections(str(x), objection_keywords))
    df['objection_transformer'] = [[] for _ in range(len(df))]  # Initialize with empty lists

    # 3.5. Filter comments that need transformer analysis (only those without keyword objections)
    comments_needing_transformer = df[df['objection_keywords'].apply(len) == 0]
    print(f"Found {len(comments_needing_transformer)} comments needing transformer analysis (out of {len(df)} total)")
    
    # 3.6. Adaptive transformer analysis limits based on system capabilities
    if torch.cuda.is_available():
        max_transformer_samples = 500  # Higher limit with GPU
    else:
        max_transformer_samples = 200  # Conservative limit for CPU
        
    if len(comments_needing_transformer) > max_transformer_samples:
        comments_needing_transformer = comments_needing_transformer.sample(n=max_transformer_samples, random_state=42)
        print(f"Limited transformer analysis to {max_transformer_samples} samples (GPU: {'✅' if torch.cuda.is_available() else '❌'})")

    # 4. Optimized transformer-based objection detection with model persistence
    print("Initializing transformer model with GPU support...")
    classifier = pipeline(
        "zero-shot-classification",
        model="valhalla/distilbart-mnli-12-1",
        device=0 if torch.cuda.is_available() else -1,
        batch_size=32 if torch.cuda.is_available() else 16
    )
    candidate_labels = list(objection_keywords.keys())
    
    # Process with optimized batching
    if len(comments_needing_transformer) > 0:
        print(f"Processing {len(comments_needing_transformer)} comments with optimized batch processing...")
        texts = comments_needing_transformer[COMMENT_COL].astype(str).tolist()
        transformer_objections = detect_transformer_objections_batch(
            texts, candidate_labels, classifier, threshold=0.4
        )
        
        # Update only the comments that needed transformer analysis (handle variable list lengths)        
        for idx, objections in zip(comments_needing_transformer.index, transformer_objections):
            df.at[idx, 'objection_transformer'] = objections
        
        # For comments not processed by transformer, use empty lists
        remaining_comments = df[~df.index.isin(comments_needing_transformer.index)]
        for idx in remaining_comments.index:
            df.at[idx, 'objection_transformer'] = []
    else:
        print("No comments need transformer analysis - all objections found via keywords")
        for idx in df.index:
            df.at[idx, 'objection_transformer'] = []

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
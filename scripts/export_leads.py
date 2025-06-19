import pandas as pd
import os
from datetime import datetime

ENRICHED_CSV = "data/comments_data_enriched.csv"
OBJECTION_CSV = "data/objection_analysis.csv"
LEADS_CSV = "data/leads.csv"
QUALIFIED_LEADS_CSV = "data/qualified_leads.csv"
REPORT_TXT = "reports/leads_summary.txt"

# Define which intents are considered leads
LEAD_INTENTS = ["Purchase Intent", "Interest/Inquiry"]

# Lead qualification criteria
PRIORITIZE_POSITIVE = True
MIN_LEAD_SCORE = 2  # Minimum score to be considered qualified

def compute_enhanced_lead_score(row, user_comment_counts, has_objections=False):
    """Enhanced lead scoring with objection analysis"""
    score = 0
    
    # Intent scoring (primary factor)
    if row["Intent"] == "Purchase Intent":
        score += 3  # Increased weight for purchase intent
    elif row["Intent"] == "Interest/Inquiry":
        score += 2
    
    # Sentiment scoring
    if row.get("Sentiment", "") == "POSITIVE":
        score += 2
    elif row.get("Sentiment", "") == "NEGATIVE":
        score -= 1  # Negative sentiment reduces score
    
    # Engagement scoring (repeat user indicates higher interest)
    user_comments = user_comment_counts.get(row["Username"], 0)
    if user_comments > 3:
        score += 2  # Very engaged user
    elif user_comments > 1:
        score += 1  # Somewhat engaged user
    
    # Objection analysis (if available)
    if has_objections and 'objections' in row:
        objections = eval(row['objections']) if isinstance(row['objections'], str) else row['objections']
        if objections and len(objections) > 0:
            # Users with objections might need more nurturing but are still valuable
            score += 0.5  # Small bonus for expressing specific concerns
    
    # Comment length (longer comments often indicate more interest)
    comment_length = len(str(row.get("Comment", "")))
    if comment_length > 100:
        score += 1
    elif comment_length > 50:
        score += 0.5
    
    # Recency bonus (more recent comments are more valuable)
    if 'Timestamp' in row:
        try:
            comment_date = pd.to_datetime(row['Timestamp'])
            days_ago = (datetime.now() - comment_date).days
            if days_ago <= 7:
                score += 1  # Recent comment bonus
            elif days_ago <= 30:
                score += 0.5
        except:
            pass
    
    return round(score, 1)

def categorize_lead_quality(score):
    """Categorize leads based on score"""
    if score >= 6:
        return "Hot Lead"
    elif score >= 4:
        return "Warm Lead"
    elif score >= 2:
        return "Cold Lead"
    else:
        return "Unqualified"

def main():
    # Load enriched data
    if not os.path.exists(ENRICHED_CSV):
        print(f"Enriched data file not found: {ENRICHED_CSV}")
        return
    
    df = pd.read_csv(ENRICHED_CSV)
    if df.empty:
        print("No data to process.")
        return
    
    # Check if objection analysis is available
    has_objection_data = os.path.exists(OBJECTION_CSV)
    if has_objection_data:
        objection_df = pd.read_csv(OBJECTION_CSV)
        # Merge objection data if available
        df = df.merge(objection_df[['Username', 'Comment', 'objections']], 
                     on=['Username', 'Comment'], how='left', suffixes=('', '_obj'))
        print("Objection analysis data integrated into lead scoring.")
    
    print(f"Processing {len(df)} total comments for lead generation...")
    
    # Filter for leads based on intent
    leads = df[df["Intent"].isin(LEAD_INTENTS)].copy()
    print(f"Found {len(leads)} comments with lead intent.")
    
    if PRIORITIZE_POSITIVE and "Sentiment" in leads.columns:
        positive_leads = leads[leads["Sentiment"] == "POSITIVE"]
        print(f"Filtered to {len(positive_leads)} positive sentiment leads.")
        leads = positive_leads
    
    if leads.empty:
        print("No qualified leads found.")
        return
    
    # Calculate engagement metrics
    user_comment_counts = df["Username"].value_counts().to_dict()
    
    # Compute enhanced lead scores
    leads["LeadScore"] = leads.apply(
        lambda row: compute_enhanced_lead_score(row, user_comment_counts, has_objection_data), 
        axis=1
    )
    
    # Add lead quality categories
    leads["LeadQuality"] = leads["LeadScore"].apply(categorize_lead_quality)
    
    # Sort by score (highest first)
    leads = leads.sort_values(by="LeadScore", ascending=False)
    
    # Create qualified leads (above minimum score)
    qualified_leads = leads[leads["LeadScore"] >= MIN_LEAD_SCORE].copy()
    
    # Select relevant fields for export
    base_fields = ["Username", "Comment", "Timestamp", "Sentiment", "Intent", "LeadScore", "LeadQuality"]
    if has_objection_data and 'objections' in leads.columns:
        base_fields.append("objections")
    
    lead_fields = [col for col in base_fields if col in leads.columns]
    
    # Export all leads
    os.makedirs("data", exist_ok=True)
    leads[lead_fields].to_csv(LEADS_CSV, index=False)
    print(f"Exported {len(leads)} total leads to {LEADS_CSV}")
    
    # Export qualified leads
    qualified_leads[lead_fields].to_csv(QUALIFIED_LEADS_CSV, index=False)
    print(f"Exported {len(qualified_leads)} qualified leads to {QUALIFIED_LEADS_CSV}")
    
    # Generate comprehensive summary report
    os.makedirs("reports", exist_ok=True)
    with open(REPORT_TXT, "w") as f:
        f.write("LEAD GENERATION SUMMARY REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall metrics
        f.write("OVERALL METRICS:\n")
        f.write(f"- Total comments processed: {len(df):,}\n")
        f.write(f"- Total leads identified: {len(leads):,}\n")
        f.write(f"- Qualified leads (score ≥ {MIN_LEAD_SCORE}): {len(qualified_leads):,}\n")
        f.write(f"- Lead conversion rate: {len(leads)/len(df)*100:.1f}%\n")
        f.write(f"- Qualification rate: {len(qualified_leads)/len(leads)*100:.1f}%\n\n")
        
        # Lead quality breakdown
        f.write("LEAD QUALITY BREAKDOWN:\n")
        quality_counts = leads["LeadQuality"].value_counts()
        for quality, count in quality_counts.items():
            f.write(f"- {quality}: {count:,} leads ({count/len(leads)*100:.1f}%)\n")
        f.write("\n")
        
        # Top scoring leads
        f.write("TOP 10 HIGHEST SCORING LEADS:\n")
        for i, (_, row) in enumerate(qualified_leads.head(10).iterrows(), 1):
            objection_info = ""
            if has_objection_data and 'objections' in row:
                objections = eval(row['objections']) if isinstance(row['objections'], str) else row['objections']
                if objections:
                    objection_info = f" | Objections: {', '.join(objections)}"
            
            f.write(f"{i:2d}. {row['Username']} (Score: {row['LeadScore']}) - {row['LeadQuality']}\n")
            f.write(f"    Intent: {row['Intent']} | Sentiment: {row['Sentiment']}{objection_info}\n")
            f.write(f"    Comment: {str(row['Comment'])[:100]}...\n\n")
        
        # Top users by lead count
        f.write("TOP 5 USERS BY LEAD COUNT:\n")
        top_users = leads["Username"].value_counts().head(5)
        for user, count in top_users.items():
            avg_score = leads[leads["Username"] == user]["LeadScore"].mean()
            f.write(f"- {user}: {count} leads (avg score: {avg_score:.1f})\n")
        f.write("\n")
        
        # Intent breakdown
        f.write("LEAD INTENT BREAKDOWN:\n")
        intent_counts = leads["Intent"].value_counts()
        for intent, count in intent_counts.items():
            avg_score = leads[leads["Intent"] == intent]["LeadScore"].mean()
            f.write(f"- {intent}: {count:,} leads (avg score: {avg_score:.1f})\n")
        
        # Objection analysis (if available)
        if has_objection_data and 'objections' in leads.columns:
            f.write("\nOBJECTION ANALYSIS:\n")
            all_objections = []
            for _, row in leads.iterrows():
                if 'objections' in row:
                    objections = eval(row['objections']) if isinstance(row['objections'], str) else row['objections']
                    if objections:
                        all_objections.extend(objections)
            
            if all_objections:
                from collections import Counter
                objection_counts = Counter(all_objections)
                f.write("Top objections among leads:\n")
                for objection, count in objection_counts.most_common(5):
                    f.write(f"- {objection}: {count} mentions\n")
            else:
                f.write("No specific objections detected among leads.\n")
    
    print(f"Comprehensive lead summary report saved to {REPORT_TXT}")
    
    # Print quick summary to console
    print("\n" + "="*50)
    print("LEAD GENERATION SUMMARY")
    print("="*50)
    print(f"Total Leads: {len(leads):,}")
    print(f"Qualified Leads: {len(qualified_leads):,}")
    print(f"Hot Leads: {len(leads[leads['LeadQuality'] == 'Hot Lead']):,}")
    print(f"Warm Leads: {len(leads[leads['LeadQuality'] == 'Warm Lead']):,}")
    print("="*50)

if __name__ == "__main__":
    main()

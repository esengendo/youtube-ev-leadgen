#!/bin/bash

# =============================================================================
# PROFESSIONAL EV LEAD GENERATION AUTOMATION PIPELINE
# =============================================================================
# Description: Complete automated pipeline for YouTube EV comment analysis,
#              lead generation, and business intelligence reporting
# Author: Data Science Team
# Version: 2.0
# =============================================================================

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="$LOG_DIR/pipeline_$TIMESTAMP.log"

# Detect environment and set Python interpreter
if [ -f /.dockerenv ] || [ -n "${DOCKER_CONTAINER}" ]; then
    # Running in Docker container
    PYTHON_CMD="python"
    log_info() {
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" | tee -a "$LOG_FILE"
    }
    log_info "🐳 Running in Docker container"
else
    # Running locally, use virtual environment
    if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
        PYTHON_CMD="$PROJECT_DIR/.venv/bin/python"
        log_info() {
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" | tee -a "$LOG_FILE"
        }
        log_info "🏠 Running locally with virtual environment"
    else
        echo "❌ ERROR: Virtual environment not found at $PROJECT_DIR/.venv/bin/python"
        echo "Please run 'uv sync' to create the virtual environment first."
        exit 1
    fi
fi

# Create logs directory
mkdir -p "$LOG_DIR"

# Logging functions
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log_error "Pipeline failed at step: $1"
    log_error "Check log file: $LOG_FILE"
    exit 1
}

# Performance tracking
start_time=$(date +%s)
step_start_time=$start_time

track_step() {
    local step_name="$1"
    local current_time=$(date +%s)
    local step_duration=$((current_time - step_start_time))
    local total_duration=$((current_time - start_time))
    
    log_success "$step_name completed in ${step_duration}s (Total: ${total_duration}s)"
    step_start_time=$current_time
}

# Business metrics tracking - using simple variables instead of associative array
RAW_COMMENTS_COUNT=0
CLEANED_COMMENTS_COUNT=0
ENRICHED_COMMENTS_COUNT=0
QUALIFIED_LEADS_COUNT=0
HIGH_PROB_LEADS_COUNT=0
OBJECTION_COMMENTS_COUNT=0
PREDICTED_LEADS_COUNT=0

# Main pipeline execution
main() {
    log_info "🚀 Starting Professional EV Lead Generation Pipeline"
    log_info "Project Directory: $PROJECT_DIR"
    log_info "Log File: $LOG_FILE"
    
    cd "$PROJECT_DIR" || handle_error "Failed to change to project directory"
    
    # Step 1: Data Ingestion
    log_info "📥 Step 1: Data Ingestion from YouTube API"
    if $PYTHON_CMD scripts/data_ingestion.py; then
        track_step "Data Ingestion"
        # Count raw comments
        if [[ -f "data/comments_data.csv" ]]; then
            RAW_COMMENTS_COUNT=$(wc -l < data/comments_data.csv)
            log_info "Raw comments collected: $RAW_COMMENTS_COUNT"
        fi
    else
        handle_error "Data Ingestion"
    fi
    
    # Step 2: Data Preprocessing
    log_info "🧹 Step 2: Data Preprocessing & Cleaning"
    if $PYTHON_CMD scripts/data_preprocessing.py; then
        track_step "Data Preprocessing"
        # Count cleaned comments
        if [[ -f "data/comments_data_cleaned.csv" ]]; then
            CLEANED_COMMENTS_COUNT=$(wc -l < data/comments_data_cleaned.csv)
            log_info "Cleaned comments: $CLEANED_COMMENTS_COUNT"
        fi
    else
        handle_error "Data Preprocessing"
    fi
    
    # Step 3: Sentiment & Intent Analysis
    log_info "🧠 Step 3: AI-Powered Sentiment & Intent Analysis"
    if $PYTHON_CMD scripts/sentiment_intent_analysis.py; then
        track_step "Sentiment & Intent Analysis"
        # Count enriched comments
        if [[ -f "data/comments_data_enriched.csv" ]]; then
            ENRICHED_COMMENTS_COUNT=$(wc -l < data/comments_data_enriched.csv)
            log_info "Enriched comments: $ENRICHED_COMMENTS_COUNT"
        fi
    else
        handle_error "Sentiment & Intent Analysis"
    fi
    
    # Step 4: Objection Analysis
    log_info "🚨 Step 4: Customer Objection Analysis"
    if $PYTHON_CMD scripts/objection_analysis.py; then
        track_step "Objection Analysis"
        # Count objections detected
        if [[ -f "data/objection_analysis.csv" ]]; then
            OBJECTION_COMMENTS_COUNT=$(wc -l < data/objection_analysis.csv)
            log_info "Comments analyzed for objections: $OBJECTION_COMMENTS_COUNT"
        fi
    else
        handle_error "Objection Analysis"
    fi
    
    # Step 5: Lead Generation & Scoring
    log_info "🎯 Step 5: Lead Generation & Qualification"
    if $PYTHON_CMD scripts/export_leads.py; then
        track_step "Lead Generation"
        # Count qualified leads
        if [[ -f "data/qualified_leads.csv" ]]; then
            QUALIFIED_LEADS_COUNT=$(wc -l < data/qualified_leads.csv)
            log_info "Qualified leads generated: $QUALIFIED_LEADS_COUNT"
        fi
    else
        handle_error "Lead Generation"
    fi
    
    # Step 6: Predictive Lead Scoring
    log_info "🤖 Step 6: ML-Powered Predictive Lead Scoring"
    if $PYTHON_CMD scripts/predictive_lead_scoring.py; then
        track_step "Predictive Lead Scoring"
        # Count high-probability leads
        if [[ -f "data/leads_predicted.csv" ]]; then
            PREDICTED_LEADS_COUNT=$(wc -l < data/leads_predicted.csv)
            log_info "Predicted leads: $PREDICTED_LEADS_COUNT"
            
            # Count high-probability leads (95%+)
            HIGH_PROB_LEADS_COUNT=$($PYTHON_CMD -c "
import pandas as pd
df = pd.read_csv('data/leads_predicted.csv')
print(len(df[df['ConversionProbability'] >= 0.95]))
" 2>/dev/null || echo "0")
            log_info "High-probability leads (95%+): $HIGH_PROB_LEADS_COUNT"
        fi
    else
        handle_error "Predictive Lead Scoring"
    fi
    
    # Step 7: Business Analytics & Alerts
    log_info "📊 Step 7: Business Analytics & Alert Generation"
    if $PYTHON_CMD scripts/analytics_and_alerts.py; then
        track_step "Business Analytics"
        log_info "Executive dashboard and alerts generated"
    else
        handle_error "Business Analytics"
    fi
    
    # Step 8: Visualization Generation
    log_info "📈 Step 8: Business Intelligence Visualizations"
    
    # Generate all visualizations
    visualization_scripts=(
        "visualize_cleaned_data.py"
        "visualize_enriched_data.py"
        "visualize_predicted_leads.py"
        "visualize_lead_trends.py"
    )
    
    for script in "${visualization_scripts[@]}"; do
        if [[ -f "scripts/$script" ]]; then
            log_info "Generating visualizations: $script"
            if $PYTHON_CMD "scripts/$script"; then
                log_info "✅ $script completed"
            else
                log_error "⚠️ $script failed (non-critical)"
            fi
        fi
    done
    
    track_step "Visualization Generation"
    
    # Step 9: Generate Business Reports
    log_info "📄 Step 9: Executive Report Generation"
    generate_executive_summary
    track_step "Executive Report Generation"
    
    # Step 10: Send Notifications (if configured)
    log_info "📧 Step 10: Stakeholder Notifications"
    if [[ -f "scripts/send_report_email.py" ]]; then
        if $PYTHON_CMD scripts/send_report_email.py; then
            log_success "Email notifications sent"
        else
            log_error "Email notifications failed (non-critical)"
        fi
    fi
    track_step "Stakeholder Notifications"
    
    # Pipeline completion
    total_time=$(($(date +%s) - start_time))
    log_success "🎉 Pipeline completed successfully in $total_time seconds"
    
    # Generate final business summary
    generate_business_summary
}

generate_executive_summary() {
    local summary_file="reports/pipeline_summary_$TIMESTAMP.txt"
    
    cat > "$summary_file" << EOF
=============================================================================
EV LEAD GENERATION PIPELINE - EXECUTIVE SUMMARY
=============================================================================
Execution Date: $(date '+%Y-%m-%d %H:%M:%S')
Pipeline Duration: $total_time seconds

📊 KEY BUSINESS METRICS:
=============================================================================
Raw Comments Collected: $RAW_COMMENTS_COUNT
Comments After Cleaning: $CLEANED_COMMENTS_COUNT
Comments Enriched with AI: $ENRICHED_COMMENTS_COUNT
Qualified Leads Generated: $QUALIFIED_LEADS_COUNT
High-Probability Leads (95%+): $HIGH_PROB_LEADS_COUNT

💰 BUSINESS IMPACT:
=============================================================================
Lead Conversion Rate: $($PYTHON_CMD -c "
qualified=$QUALIFIED_LEADS_COUNT
raw=$RAW_COMMENTS_COUNT
print(f'{qualified/max(raw,1)*100:.1f}%')
" 2>/dev/null || echo "N/A")

Revenue Potential (High-Prob): \$$($PYTHON_CMD -c "
print(f'{HIGH_PROB_LEADS_COUNT * 45000:,}')
" 2>/dev/null || echo "0")

Monthly Lead Value Estimate: \$$($PYTHON_CMD -c "
print(f'{QUALIFIED_LEADS_COUNT * 2500:,}')
" 2>/dev/null || echo "0")

🎯 PIPELINE PERFORMANCE:
=============================================================================
Data Quality Rate: $($PYTHON_CMD -c "
cleaned=$CLEANED_COMMENTS_COUNT
raw=$RAW_COMMENTS_COUNT
print(f'{cleaned/max(raw,1)*100:.1f}%')
" 2>/dev/null || echo "N/A")

AI Processing Success: $($PYTHON_CMD -c "
enriched=$ENRICHED_COMMENTS_COUNT
cleaned=$CLEANED_COMMENTS_COUNT
print(f'{enriched/max(cleaned,1)*100:.1f}%')
" 2>/dev/null || echo "N/A")

Lead Qualification Rate: $($PYTHON_CMD -c "
qualified=$QUALIFIED_LEADS_COUNT
enriched=$ENRICHED_COMMENTS_COUNT
print(f'{qualified/max(enriched,1)*100:.1f}%')
" 2>/dev/null || echo "N/A")

📁 OUTPUT FILES:
=============================================================================
- Raw Data: data/comments_data.csv
- Cleaned Data: data/comments_data_cleaned.csv
- Enriched Data: data/comments_data_enriched.csv
- Qualified Leads: data/qualified_leads.csv
- Predicted Leads: data/leads_predicted.csv
- Executive Dashboard: reports/executive_dashboard.txt
- Visualizations: visualizations/*.html, visualizations/*.png

🚀 NEXT ACTIONS:
=============================================================================
1. Review high-probability leads in data/leads_predicted.csv
2. Check executive dashboard: reports/executive_dashboard.txt
3. Monitor alerts in reports/alerts_log.json
4. Launch Streamlit dashboard: streamlit run dashboard/streamlit_dashboard.py

=============================================================================
EOF

    log_info "Executive summary saved: $summary_file"
}

generate_business_summary() {
    log_info ""
    log_info "🎯 BUSINESS RESULTS SUMMARY:"
    log_info "================================"
    log_info "📊 Total Qualified Leads: $QUALIFIED_LEADS_COUNT"
    log_info "🔥 High-Probability Leads: $HIGH_PROB_LEADS_COUNT"
    log_info "💰 Revenue Potential: \$$($PYTHON_CMD -c "print(f'{HIGH_PROB_LEADS_COUNT * 45000:,}')" 2>/dev/null || echo "0")"
    log_info "⏱️  Total Processing Time: $total_time seconds"
    log_info ""
    log_info "📄 Reports Generated:"
    log_info "   - Executive Dashboard: reports/executive_dashboard.txt"
    log_info "   - Pipeline Summary: reports/pipeline_summary_$TIMESTAMP.txt"
    log_info "   - Detailed Logs: $LOG_FILE"
    log_info ""
    log_info "🚀 To view interactive dashboard:"
    log_info "   streamlit run dashboard/streamlit_dashboard.py"
    log_info ""
}

# Cleanup function
cleanup() {
    log_info "🧹 Performing cleanup..."
    # Add any cleanup tasks here
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Execute main pipeline
main "$@"

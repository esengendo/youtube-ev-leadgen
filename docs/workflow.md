# YouTube EV Lead Generation Pipeline — Workflow Documentation

## Overview
This document describes the end-to-end workflow for the YouTube EV Lead Generation project, designed to drive actionable insights for marketing, sales, and revenue growth.

---

## Pipeline Steps

### 1. Data Ingestion
- **Script:** `scripts/data_ingestion.py`
- **Description:** Fetches YouTube comments from specified playlists/videos and saves them to `data/comments_data.csv`.

### 2. Data Preprocessing
- **Script:** `scripts/data_preprocessing.py`
- **Description:** Cleans and normalizes comments, removes duplicates, and saves to `data/comments_data_cleaned.csv`.

### 3. Sentiment & Intent Analysis
- **Script:** `scripts/sentiment_intent_analysis.py`
- **Description:** Assigns sentiment and intent labels to each comment using a transformer model and business rules. Output: `data/comments_data_enriched.csv`.

### 4. Visualization
- **Scripts:**
  - `scripts/visualize_cleaned_data.py` (general comment analytics)
  - `scripts/visualize_enriched_data.py` (sentiment/intent analytics)
  - `scripts/visualize_lead_trends.py` (lead trends over time)
- **Description:** Generates interactive HTML visualizations in `visualizations/`.

### 5. Lead Export & Scoring
- **Script:** `scripts/export_leads.py`
- **Description:** Filters and scores leads, exports to `data/leads.csv`, and generates a summary report in `reports/leads_summary.txt`.

### 6. Automated Email Reporting
- **Script:** `scripts/send_report_email.py`
- **Description:** Emails the summary report to the marketing/sales team using Gmail. Configure credentials in `.env`.

---

## Automation
- **Scheduling:** Use `cron` (macOS/Linux) or Task Scheduler (Windows) to run the pipeline and email script at regular intervals.
- **Example cron entry:**
  ```bash
  0 8 * * * cd /path/to/youtube-ev-leadgen && uv run scripts/export_leads.py && uv run scripts/send_report_email.py
  ```

---

## Configuration
- **Environment variables:**
  - `GMAIL_ADDRESS`: Gmail address for sending reports
  - `GMAIL_APP_PASSWORD`: App password for Gmail
  - `REPORT_RECIPIENT_EMAIL`: Recipient email address
- **Set these in your `.env` file.**

---

## Handoff Checklist
- [ ] All scripts tested and working
- [ ] `.env` configured with correct credentials
- [ ] Data and reports directories present
- [ ] Visualizations generated and saved
- [ ] Documentation up to date (`docs/session_summary.md`, `docs/workflow.md`)

---

## Extending the Workflow
- Integrate with a CRM or marketing automation tool (see `export_leads.py` for lead export logic)
- Refine lead scoring as business needs evolve
- Add more advanced analytics or dashboards as required

---

*For questions or further development, refer to this documentation or contact the project owner.*

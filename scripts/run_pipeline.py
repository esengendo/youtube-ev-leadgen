#!/usr/bin/env python3
"""
Professional EV Lead Generation Automation Pipeline
Using UV for environment management and Python for orchestration
"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

class PipelineRunner:
    def __init__(self):
        self.start_time = time.time()
        self.project_dir = Path(__file__).parent.parent
        self.logs_dir = self.project_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.logs_dir / f"pipeline_{timestamp}.log"
        
        # Metrics tracking
        self.metrics = {
            'raw_comments': 0,
            'cleaned_comments': 0,
            'enriched_comments': 0,
            'qualified_leads': 0,
            'high_prob_leads': 0,
            'objection_comments': 0,
            'predicted_leads': 0
        }
        
        self.log_info("🚀 Starting Professional EV Lead Generation Pipeline")
        self.log_info(f"Project Directory: {self.project_dir}")
        self.log_info(f"Log File: {self.log_file}")

    def log_info(self, message):
        """Log info message to both console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] INFO: {message}"
        print(log_message)
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')

    def log_error(self, message):
        """Log error message to both console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] ERROR: {message}"
        print(log_message, file=sys.stderr)
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')

    def log_success(self, message):
        """Log success message to both console and file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] SUCCESS: {message}"
        print(log_message)
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')

    def run_uv_script(self, script_path, description):
        """Run a Python script using UV"""
        step_start = time.time()
        self.log_info(f"📥 {description}")
        
        try:
            # Change to project directory
            os.chdir(self.project_dir)
            
            # Run script with UV
            result = subprocess.run(
                ["uv", "run", "python", script_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            step_duration = time.time() - step_start
            self.log_success(f"{description} completed in {step_duration:.1f}s")
            
            if result.stdout:
                self.log_info(f"Output: {result.stdout.strip()}")
                
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_error(f"{description} failed: {e}")
            if e.stdout:
                self.log_error(f"stdout: {e.stdout}")
            if e.stderr:
                self.log_error(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            self.log_error(f"{description} failed with exception: {e}")
            return False

    def count_csv_rows(self, file_path):
        """Count rows in CSV file (excluding header)"""
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                return len(df)
            return 0
        except Exception as e:
            self.log_error(f"Error counting rows in {file_path}: {e}")
            return 0

    def update_metrics_from_files(self):
        """Update metrics by counting rows in data files"""
        data_files = {
            'raw_comments': 'data/comments_data.csv',
            'cleaned_comments': 'data/comments_data_cleaned.csv',
            'enriched_comments': 'data/comments_data_enriched.csv',
            'qualified_leads': 'data/qualified_leads.csv',
            'predicted_leads': 'data/leads_predicted.csv',
            'objection_comments': 'data/objection_analysis.csv'
        }
        
        for metric, file_path in data_files.items():
            self.metrics[metric] = self.count_csv_rows(file_path)
            self.log_info(f"{metric.replace('_', ' ').title()}: {self.metrics[metric]}")

    def calculate_high_prob_leads(self):
        """Calculate high probability leads (95%+)"""
        try:
            leads_file = 'data/leads_predicted.csv'
            if os.path.exists(leads_file):
                df = pd.read_csv(leads_file)
                if 'ConversionProbability' in df.columns:
                    high_prob = len(df[df['ConversionProbability'] >= 0.95])
                    self.metrics['high_prob_leads'] = high_prob
                    self.log_info(f"High-probability leads (95%+): {high_prob}")
        except Exception as e:
            self.log_error(f"Error calculating high probability leads: {e}")

    def run_pipeline(self):
        """Execute the complete pipeline"""
        
        # Pipeline steps
        steps = [
            ("scripts/data_ingestion.py", "Step 1: Data Ingestion from YouTube API"),
            ("scripts/data_preprocessing.py", "Step 2: Data Preprocessing & Cleaning"),
            ("scripts/sentiment_intent_analysis.py", "Step 3: AI-Powered Sentiment & Intent Analysis"),
            ("scripts/objection_analysis.py", "Step 4: Customer Objection Analysis"),
            ("scripts/export_leads.py", "Step 5: Lead Generation & Qualification"),
            ("scripts/predictive_lead_scoring.py", "Step 6: ML-Powered Predictive Lead Scoring"),
            ("scripts/analytics_and_alerts.py", "Step 7: Business Analytics & Alert Generation"),
        ]
        
        # Execute each step
        for script_path, description in steps:
            if not self.run_uv_script(script_path, description):
                self.log_error(f"Pipeline failed at: {description}")
                return False
            
            # Update metrics after each step
            self.update_metrics_from_files()
        
        # Step 8: Visualization Generation
        self.log_info("📈 Step 8: Business Intelligence Visualizations")
        visualization_scripts = [
            "scripts/visualize_cleaned_data.py",
            "scripts/visualize_enriched_data.py", 
            "scripts/visualize_predicted_leads.py",
            "scripts/visualize_lead_trends.py"
        ]
        
        for script in visualization_scripts:
            if os.path.exists(script):
                if self.run_uv_script(script, f"Generating visualizations: {script}"):
                    self.log_info(f"✅ {script} completed")
                else:
                    self.log_error(f"⚠️ {script} failed (non-critical)")
        
        # Step 9: Calculate final metrics
        self.calculate_high_prob_leads()
        
        # Step 10: Generate reports
        self.generate_executive_summary()
        
        # Step 11: Send notifications (optional)
        self.log_info("📧 Step 10: Stakeholder Notifications")
        if os.path.exists("scripts/send_report_email.py"):
            if self.run_uv_script("scripts/send_report_email.py", "Email notifications"):
                self.log_success("Email notifications sent")
            else:
                self.log_error("Email notifications failed (non-critical)")
        
        # Pipeline completion
        total_time = time.time() - self.start_time
        self.log_success(f"🎉 Pipeline completed successfully in {total_time:.1f} seconds")
        
        # Generate final business summary
        self.generate_business_summary()
        
        return True

    def generate_executive_summary(self):
        """Generate executive summary report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.project_dir / "reports" / f"pipeline_summary_{timestamp}.txt"
        summary_file.parent.mkdir(exist_ok=True)
        
        total_time = time.time() - self.start_time
        
        # Calculate business metrics
        conversion_rate = (self.metrics['qualified_leads'] / max(self.metrics['raw_comments'], 1)) * 100
        revenue_potential = self.metrics['high_prob_leads'] * 45000
        monthly_value = self.metrics['qualified_leads'] * 2500
        data_quality_rate = (self.metrics['cleaned_comments'] / max(self.metrics['raw_comments'], 1)) * 100
        ai_success_rate = (self.metrics['enriched_comments'] / max(self.metrics['cleaned_comments'], 1)) * 100
        qualification_rate = (self.metrics['qualified_leads'] / max(self.metrics['enriched_comments'], 1)) * 100
        
        summary_content = f"""
=============================================================================
EV LEAD GENERATION PIPELINE - EXECUTIVE SUMMARY
=============================================================================
Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Pipeline Duration: {total_time:.1f} seconds

📊 KEY BUSINESS METRICS:
=============================================================================
Raw Comments Collected: {self.metrics['raw_comments']:,}
Comments After Cleaning: {self.metrics['cleaned_comments']:,}
Comments Enriched with AI: {self.metrics['enriched_comments']:,}
Qualified Leads Generated: {self.metrics['qualified_leads']:,}
High-Probability Leads (95%+): {self.metrics['high_prob_leads']:,}

💰 BUSINESS IMPACT:
=============================================================================
Lead Conversion Rate: {conversion_rate:.1f}%
Revenue Potential (High-Prob): ${revenue_potential:,}
Monthly Lead Value Estimate: ${monthly_value:,}

🎯 PIPELINE PERFORMANCE:
=============================================================================
Data Quality Rate: {data_quality_rate:.1f}%
AI Processing Success: {ai_success_rate:.1f}%
Lead Qualification Rate: {qualification_rate:.1f}%

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
4. Launch Streamlit dashboard: uv run streamlit run dashboard/streamlit_dashboard.py

=============================================================================
        """
        
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        
        self.log_info(f"Executive summary saved: {summary_file}")

    def generate_business_summary(self):
        """Generate final business summary"""
        total_time = time.time() - self.start_time
        revenue_potential = self.metrics['high_prob_leads'] * 45000
        
        self.log_info("")
        self.log_info("🎯 BUSINESS RESULTS SUMMARY:")
        self.log_info("================================")
        self.log_info(f"📊 Total Qualified Leads: {self.metrics['qualified_leads']:,}")
        self.log_info(f"🔥 High-Probability Leads: {self.metrics['high_prob_leads']:,}")
        self.log_info(f"💰 Revenue Potential: ${revenue_potential:,}")
        self.log_info(f"⏱️  Total Processing Time: {total_time:.1f} seconds")
        self.log_info("")
        self.log_info("📄 Reports Generated:")
        self.log_info("   - Executive Dashboard: reports/executive_dashboard.txt")
        self.log_info(f"   - Pipeline Summary: reports/pipeline_summary_*.txt")
        self.log_info(f"   - Detailed Logs: {self.log_file}")
        self.log_info("")
        self.log_info("🚀 To view interactive dashboard:")
        self.log_info("   uv run streamlit run dashboard/streamlit_dashboard.py")
        self.log_info("")

def main():
    """Main entry point"""
    try:
        pipeline = PipelineRunner()
        success = pipeline.run_pipeline()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
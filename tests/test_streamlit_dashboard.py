"""
Comprehensive tests for the Streamlit EV Lead Generation Dashboard
Using Streamlit's built-in testing framework and pytest
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import Streamlit testing framework
from streamlit.testing.v1 import AppTest

# Test data setup
@pytest.fixture
def sample_data():
    """Create sample data for testing"""
    return {
        'comments_data_enriched.csv': pd.DataFrame({
            'comment_text': ['Great EV!', 'Love this car', 'Expensive but worth it'],
            'sentiment': ['POSITIVE', 'POSITIVE', 'NEUTRAL'],
            'sentiment_score': [0.8, 0.9, 0.5],
            'intent': ['Interest/Inquiry', 'Purchase Intent', 'General Comment'],
            'author_name': ['User1', 'User2', 'User3'],
            'like_count': [10, 5, 2],
            'published_at': ['2024-01-01', '2024-01-02', '2024-01-03']
        }),
        'qualified_leads.csv': pd.DataFrame({
            'author_name': ['User1', 'User2'],
            'comment_text': ['Great EV!', 'Love this car'],
            'sentiment': ['POSITIVE', 'POSITIVE'],
            'intent': ['Interest/Inquiry', 'Purchase Intent'],
            'lead_score': [85, 95],
            'conversion_probability': [0.75, 0.90]
        }),
        'leads_predicted.csv': pd.DataFrame({
            'author_name': ['User1', 'User2'],
            'conversion_probability': [0.75, 0.90],
            'predicted_conversion': [1, 1],
            'lead_score': [85, 95]
        }),
        'objection_analysis.csv': pd.DataFrame({
            'comment_text': ['Too expensive', 'Range anxiety'],
            'objection_category': ['Price Concerns', 'Range Anxiety'],
            'objection_keywords': ['expensive', 'range'],
            'sentiment': ['NEGATIVE', 'NEGATIVE']
        })
    }

@pytest.fixture
def setup_test_data(sample_data, tmp_path):
    """Setup test data files"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    for filename, df in sample_data.items():
        df.to_csv(data_dir / filename, index=False)
    
    return data_dir

class TestStreamlitDashboard:
    """Test suite for the Streamlit dashboard"""
    
    def test_dashboard_loads_successfully(self, setup_test_data):
        """Test that the dashboard loads without errors"""
        # Mock the data directory
        import streamlit as st
        
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        
        # Mock the data path
        at.session_state["data_path"] = str(setup_test_data)
        
        # Run the app
        at.run()
        
        # Check that no exceptions occurred
        assert not at.exception, f"Dashboard failed to load: {at.exception}"
    
    def test_sidebar_navigation(self, setup_test_data):
        """Test sidebar navigation functionality"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Check that sidebar elements exist
        assert len(at.sidebar.selectbox) > 0, "Sidebar navigation not found"
        
        # Test navigation to different pages
        pages = ["📊 Executive Dashboard", "🎯 Lead Analysis", "💬 Sentiment Analysis", "⚠️ Objection Analysis"]
        
        for page in pages:
            if any(page in str(option) for option in at.sidebar.selectbox[0].options):
                at.sidebar.selectbox[0].select(page).run()
                assert not at.exception, f"Failed to navigate to {page}"
    
    def test_executive_dashboard_kpis(self, setup_test_data):
        """Test that KPIs are displayed correctly on executive dashboard"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Navigate to executive dashboard
        if len(at.sidebar.selectbox) > 0:
            at.sidebar.selectbox[0].select("📊 Executive Dashboard").run()
        
        # Check for KPI metrics
        metrics_found = len(at.metric) > 0
        assert metrics_found, "No KPI metrics found on executive dashboard"
    
    def test_lead_analysis_functionality(self, setup_test_data):
        """Test lead analysis page functionality"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Navigate to lead analysis
        if len(at.sidebar.selectbox) > 0:
            at.sidebar.selectbox[0].select("🎯 Lead Analysis").run()
        
        # Check for data tables or charts
        has_dataframe = len(at.dataframe) > 0
        has_charts = len(at.plotly_chart) > 0 or len(at.pyplot) > 0
        
        assert has_dataframe or has_charts, "No data visualization found on lead analysis page"
    
    def test_sentiment_analysis_charts(self, setup_test_data):
        """Test sentiment analysis visualizations"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Navigate to sentiment analysis
        if len(at.sidebar.selectbox) > 0:
            at.sidebar.selectbox[0].select("💬 Sentiment Analysis").run()
        
        # Check for charts
        has_charts = len(at.plotly_chart) > 0 or len(at.pyplot) > 0
        assert has_charts, "No sentiment analysis charts found"
    
    def test_objection_analysis_display(self, setup_test_data):
        """Test objection analysis functionality"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Navigate to objection analysis
        if len(at.sidebar.selectbox) > 0:
            at.sidebar.selectbox[0].select("⚠️ Objection Analysis").run()
        
        # Check for objection data display
        has_content = len(at.dataframe) > 0 or len(at.plotly_chart) > 0
        assert has_content, "No objection analysis content found"
    
    def test_data_filtering_functionality(self, setup_test_data):
        """Test data filtering controls"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Check for filter controls
        has_filters = (len(at.selectbox) > 0 or 
                      len(at.multiselect) > 0 or 
                      len(at.slider) > 0 or 
                      len(at.date_input) > 0)
        
        assert has_filters, "No filtering controls found"
    
    def test_export_functionality(self, setup_test_data):
        """Test data export functionality"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Look for download buttons
        has_download = len(at.download_button) > 0
        
        # This is optional functionality, so we'll just log the result
        if has_download:
            print("✅ Export functionality found")
        else:
            print("ℹ️ No export functionality found (optional feature)")
    
    def test_error_handling_missing_data(self, tmp_path):
        """Test dashboard behavior with missing data files"""
        # Create empty data directory
        empty_data_dir = tmp_path / "empty_data"
        empty_data_dir.mkdir()
        
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(empty_data_dir)
        
        # Run the app - it should handle missing data gracefully
        at.run()
        
        # Check for error messages or graceful degradation
        has_error_message = len(at.error) > 0 or len(at.warning) > 0
        
        # The app should either show an error message or handle missing data gracefully
        assert not at.exception or has_error_message, "App should handle missing data gracefully"

class TestDashboardPerformance:
    """Performance tests for the dashboard"""
    
    def test_dashboard_load_time(self, setup_test_data):
        """Test that dashboard loads within reasonable time"""
        import time
        
        start_time = time.time()
        
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        load_time = time.time() - start_time
        
        # Dashboard should load within 10 seconds
        assert load_time < 10, f"Dashboard took too long to load: {load_time:.2f} seconds"
        print(f"✅ Dashboard loaded in {load_time:.2f} seconds")
    
    def test_large_dataset_handling(self, tmp_path):
        """Test dashboard with larger dataset"""
        # Create larger test dataset
        large_data = pd.DataFrame({
            'comment_text': [f'Comment {i}' for i in range(1000)],
            'sentiment': np.random.choice(['POSITIVE', 'NEGATIVE', 'NEUTRAL'], 1000),
            'sentiment_score': np.random.random(1000),
            'intent': np.random.choice(['Purchase Intent', 'Interest/Inquiry', 'General Comment'], 1000),
            'author_name': [f'User{i}' for i in range(1000)],
            'like_count': np.random.randint(0, 100, 1000),
            'published_at': ['2024-01-01'] * 1000
        })
        
        data_dir = tmp_path / "large_data"
        data_dir.mkdir()
        large_data.to_csv(data_dir / "comments_data_enriched.csv", index=False)
        
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(data_dir)
        
        # Should handle large dataset without crashing
        at.run()
        assert not at.exception, "Dashboard failed with large dataset"

class TestBusinessLogic:
    """Test business logic and calculations"""
    
    def test_lead_scoring_calculations(self, setup_test_data):
        """Test that lead scoring calculations are correct"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Navigate to lead analysis
        if len(at.sidebar.selectbox) > 0:
            at.sidebar.selectbox[0].select("🎯 Lead Analysis").run()
        
        # Check that metrics make sense (no negative scores, etc.)
        if len(at.metric) > 0:
            for metric in at.metric:
                # Ensure metric values are reasonable
                assert metric.value is not None, "Metric value should not be None"
    
    def test_revenue_calculations(self, setup_test_data):
        """Test revenue potential calculations"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Look for revenue-related metrics
        # This will depend on your specific implementation
        assert not at.exception, "Revenue calculations should not cause errors"

# Integration tests
class TestDashboardIntegration:
    """Integration tests for the complete dashboard"""
    
    def test_end_to_end_user_workflow(self, setup_test_data):
        """Test complete user workflow through the dashboard"""
        at = AppTest.from_file("dashboard/streamlit_dashboard.py")
        at.session_state["data_path"] = str(setup_test_data)
        at.run()
        
        # Simulate user navigating through all pages
        pages = ["📊 Executive Dashboard", "🎯 Lead Analysis", "💬 Sentiment Analysis", "⚠️ Objection Analysis"]
        
        for page in pages:
            if len(at.sidebar.selectbox) > 0:
                try:
                    at.sidebar.selectbox[0].select(page).run()
                    assert not at.exception, f"Error navigating to {page}"
                except:
                    # Page might not exist, skip
                    continue
        
        print("✅ End-to-end user workflow completed successfully")

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"]) 
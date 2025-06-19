"""
Browser-based integration tests for Streamlit dashboard using Playwright
Based on: https://www.stefsmeets.nl/posts/streamlit-pytest/
"""

import pytest
import subprocess as sp
import time
import requests
from playwright.sync_api import Page, expect

# Configuration
PORT = "8502"  # Use different port to avoid conflicts
BASE_URL = f"http://localhost:{PORT}"

@pytest.fixture(scope="module", autouse=True)
def run_streamlit():
    """Run the Streamlit app for testing"""
    print(f"Starting Streamlit on port {PORT}...")
    
    # Start Streamlit process
    p = sp.Popen([
        "streamlit", "run", "dashboard/streamlit_dashboard.py",
        "--server.port", PORT,
        "--server.headless", "true",
        "--server.runOnSave", "false",
        "--server.address", "localhost"
    ])
    
    # Wait for Streamlit to start
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/_stcore/health", timeout=1)
            if response.status_code == 200:
                print(f"✅ Streamlit started successfully on {BASE_URL}")
                break
        except requests.exceptions.RequestException:
            if attempt < max_attempts - 1:
                time.sleep(1)
                continue
            else:
                p.kill()
                raise Exception("Failed to start Streamlit")
    
    yield
    
    # Cleanup
    print("Stopping Streamlit...")
    p.kill()
    p.wait()

class TestStreamlitBrowser:
    """Browser-based tests for Streamlit dashboard"""
    
    def test_page_loads_successfully(self, page: Page):
        """Test that the main page loads without errors"""
        page.goto(BASE_URL)
        
        # Wait for Streamlit to finish loading
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Check page title
        expect(page).to_have_title("streamlit_dashboard")
        
        # Check that main content is visible
        expect(page.locator("div[data-testid='stApp']")).to_be_visible()
    
    def test_sidebar_navigation(self, page: Page):
        """Test sidebar navigation functionality"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Check if sidebar exists
        sidebar = page.locator("section[data-testid='stSidebar']")
        expect(sidebar).to_be_visible()
        
        # Look for navigation elements
        selectbox = page.locator("div[data-testid='stSelectbox']").first
        if selectbox.is_visible():
            # Click on selectbox to open options
            selectbox.click()
            
            # Wait a moment for options to appear
            page.wait_for_timeout(1000)
            
            # Check if options are available
            options = page.locator("div[data-baseweb='select'] li")
            if options.count() > 0:
                print(f"✅ Found {options.count()} navigation options")
    
    def test_dashboard_interactivity(self, page: Page):
        """Test interactive elements on the dashboard"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Look for interactive elements
        buttons = page.locator("button[data-testid='baseButton-secondary']")
        selectboxes = page.locator("div[data-testid='stSelectbox']")
        sliders = page.locator("div[data-testid='stSlider']")
        
        interactive_elements = buttons.count() + selectboxes.count() + sliders.count()
        
        assert interactive_elements > 0, "No interactive elements found on dashboard"
        print(f"✅ Found {interactive_elements} interactive elements")
    
    def test_data_visualization_elements(self, page: Page):
        """Test that data visualizations are present"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Wait for content to load
        page.wait_for_timeout(3000)
        
        # Look for various visualization elements
        plotly_charts = page.locator("div[data-testid='stPlotlyChart']")
        dataframes = page.locator("div[data-testid='stDataFrame']")
        metrics = page.locator("div[data-testid='metric-container']")
        
        total_visualizations = plotly_charts.count() + dataframes.count() + metrics.count()
        
        assert total_visualizations > 0, "No data visualizations found"
        print(f"✅ Found {total_visualizations} data visualization elements")
    
    def test_responsive_design(self, page: Page):
        """Test dashboard responsiveness on different screen sizes"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Test different viewport sizes
        viewports = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 1024, "height": 768},   # Tablet
            {"width": 375, "height": 667}     # Mobile
        ]
        
        for viewport in viewports:
            page.set_viewport_size(viewport)
            page.wait_for_timeout(1000)
            
            # Check that main content is still visible
            main_content = page.locator("div[data-testid='stApp']")
            expect(main_content).to_be_visible()
            
            print(f"✅ Dashboard responsive at {viewport['width']}x{viewport['height']}")
    
    def test_error_handling(self, page: Page):
        """Test error handling in the dashboard"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Look for error messages or warnings
        errors = page.locator("div[data-testid='stException']")
        warnings = page.locator("div[data-testid='stAlert']")
        
        # Dashboard should not have critical errors
        assert errors.count() == 0, f"Found {errors.count()} errors on dashboard"
        
        if warnings.count() > 0:
            print(f"ℹ️ Found {warnings.count()} warnings (may be expected)")
        else:
            print("✅ No errors or warnings found")
    
    def test_performance_metrics(self, page: Page):
        """Test dashboard performance metrics"""
        # Measure page load time
        start_time = time.time()
        
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Wait for all content to load
        page.wait_for_timeout(2000)
        
        load_time = time.time() - start_time
        
        # Dashboard should load within reasonable time
        assert load_time < 30, f"Dashboard took too long to load: {load_time:.2f} seconds"
        print(f"✅ Dashboard loaded in {load_time:.2f} seconds")
    
    def test_accessibility_basics(self, page: Page):
        """Test basic accessibility features"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Check for basic accessibility elements
        headings = page.locator("h1, h2, h3, h4, h5, h6")
        buttons = page.locator("button")
        
        # Should have some structure
        assert headings.count() > 0, "No headings found for accessibility"
        
        # Check that buttons have accessible text
        for i in range(min(buttons.count(), 5)):  # Check first 5 buttons
            button = buttons.nth(i)
            if button.is_visible():
                text_content = button.text_content()
                assert text_content and text_content.strip(), f"Button {i} has no accessible text"
        
        print("✅ Basic accessibility checks passed")

class TestDashboardFunctionality:
    """Test specific dashboard functionality"""
    
    def test_data_filtering(self, page: Page):
        """Test data filtering functionality"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Look for filter controls
        selectboxes = page.locator("div[data-testid='stSelectbox']")
        multiselects = page.locator("div[data-testid='stMultiSelect']")
        
        if selectboxes.count() > 0:
            # Try interacting with first selectbox
            first_selectbox = selectboxes.first
            first_selectbox.click()
            page.wait_for_timeout(1000)
            
            # Look for options
            options = page.locator("div[data-baseweb='select'] li")
            if options.count() > 1:
                # Select second option
                options.nth(1).click()
                page.wait_for_timeout(2000)
                
                print("✅ Filter interaction successful")
    
    def test_export_functionality(self, page: Page):
        """Test data export functionality if available"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Look for download buttons
        download_buttons = page.locator("button").filter(has_text="Download")
        
        if download_buttons.count() > 0:
            print(f"✅ Found {download_buttons.count()} download buttons")
        else:
            print("ℹ️ No download functionality found (optional feature)")
    
    def test_real_time_updates(self, page: Page):
        """Test if dashboard updates properly"""
        page.goto(BASE_URL)
        page.get_by_text("Running...").wait_for(state="detached", timeout=30000)
        
        # Take initial screenshot for comparison
        initial_content = page.locator("div[data-testid='stApp']").inner_html()
        
        # Interact with controls if available
        buttons = page.locator("button[data-testid='baseButton-secondary']")
        if buttons.count() > 0:
            buttons.first.click()
            page.wait_for_timeout(2000)
            
            # Check if content changed
            updated_content = page.locator("div[data-testid='stApp']").inner_html()
            
            if initial_content != updated_content:
                print("✅ Dashboard updates dynamically")
            else:
                print("ℹ️ No dynamic updates detected")

if __name__ == "__main__":
    # Run browser tests
    pytest.main([__file__, "-v", "--headed"])  # Use --headed to see browser 
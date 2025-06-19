#!/usr/bin/env python3
"""
Test Runner for EV Lead Generation Dashboard
Provides easy commands to run different types of tests
"""

import subprocess
import sys
import time
import requests
import argparse
from pathlib import Path

def check_streamlit_running(port=8501):
    """Check if Streamlit is running on the specified port"""
    try:
        response = requests.get(f"http://localhost:{port}/_stcore/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def run_unit_tests():
    """Run unit tests using Streamlit's testing framework"""
    print("🧪 Running unit tests...")
    cmd = ["python", "-m", "pytest", "tests/test_streamlit_dashboard.py", "-v", "-m", "not browser"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def run_browser_tests():
    """Run browser-based integration tests"""
    print("🌐 Running browser tests...")
    
    # Install playwright browsers if needed
    print("Installing Playwright browsers...")
    subprocess.run(["python", "-m", "playwright", "install", "chromium"], 
                  capture_output=True)
    
    cmd = ["python", "-m", "pytest", "tests/test_streamlit_browser.py", "-v", "--headed"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def run_manual_test():
    """Run manual test by starting Streamlit and opening browser"""
    print("🚀 Starting Streamlit for manual testing...")
    
    if check_streamlit_running():
        print("✅ Streamlit is already running at http://localhost:8501")
        print("Open your browser and test the dashboard manually")
        return True
    
    print("Starting Streamlit dashboard...")
    print("Dashboard will be available at: http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            "streamlit", "run", "dashboard/streamlit_dashboard.py",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n✅ Streamlit stopped")
        return True

def run_performance_test():
    """Run performance tests"""
    print("⚡ Running performance tests...")
    
    # Check if dashboard loads quickly
    start_time = time.time()
    
    if not check_streamlit_running():
        print("❌ Streamlit is not running. Please start it first with: python test_runner.py --manual")
        return False
    
    load_time = time.time() - start_time
    print(f"✅ Dashboard health check completed in {load_time:.2f} seconds")
    
    # Run specific performance tests
    cmd = ["python", "-m", "pytest", "tests/test_streamlit_dashboard.py::TestDashboardPerformance", "-v"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0

def run_all_tests():
    """Run all tests in sequence"""
    print("🎯 Running complete test suite...")
    
    tests = [
        ("Unit Tests", run_unit_tests),
        ("Performance Tests", run_performance_test),
        ("Browser Tests", run_browser_tests),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name}")
        print('='*50)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

def install_test_dependencies():
    """Install testing dependencies"""
    print("📦 Installing test dependencies...")
    
    dependencies = [
        "pytest>=7.4.0",
        "pytest-playwright>=0.4.0",
        "pytest-cov>=4.1.0",
        "requests>=2.31.0"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        result = subprocess.run(["uv", "add", dep], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to install {dep}")
            print(result.stderr)
            return False
    
    # Install Playwright browsers
    print("Installing Playwright browsers...")
    subprocess.run(["python", "-m", "playwright", "install", "chromium"])
    
    print("✅ All test dependencies installed successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Test Runner for EV Lead Generation Dashboard")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--browser", action="store_true", help="Run browser tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--manual", action="store_true", help="Start Streamlit for manual testing")
    parser.add_argument("--all", action="store_true", help="Run all automated tests")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    
    args = parser.parse_args()
    
    # If no specific test type is specified, show help
    if not any([args.unit, args.browser, args.performance, args.manual, args.all, args.install]):
        parser.print_help()
        print("\n🎯 Quick Start:")
        print("1. Install dependencies: python test_runner.py --install")
        print("2. Run manual test: python test_runner.py --manual")
        print("3. Run all tests: python test_runner.py --all")
        return
    
    if args.install:
        install_test_dependencies()
        return
    
    if args.manual:
        run_manual_test()
        return
    
    if args.unit:
        success = run_unit_tests()
    elif args.browser:
        success = run_browser_tests()
    elif args.performance:
        success = run_performance_test()
    elif args.all:
        success = run_all_tests()
    else:
        parser.print_help()
        return
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 
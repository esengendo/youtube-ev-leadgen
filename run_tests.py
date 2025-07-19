#!/usr/bin/env python3
"""
Test runner for the YouTube EV Lead Generation Pipeline
Runs comprehensive unit tests and integration tests
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run all tests with comprehensive reporting"""
    
    print("🧪 Starting YouTube EV Lead Generation Pipeline Tests")
    print("=" * 60)
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Test commands to run
    test_commands = [
        # Unit tests
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        
        # Coverage report
        ["python", "-m", "pytest", "tests/", "--cov=scripts", "--cov-report=term-missing"],
        
        # Type checking (if mypy is available)
        ["python", "-m", "mypy", "scripts/", "--ignore-missing-imports"],
        
        # Code style checking (if flake8 is available)
        ["python", "-m", "flake8", "scripts/", "--max-line-length=88", "--ignore=E203,W503"],
    ]
    
    results = []
    
    for i, cmd in enumerate(test_commands, 1):
        test_name = cmd[2] if len(cmd) > 2 else cmd[1]
        print(f"\n📋 Running Test {i}: {test_name}")
        print("-" * 40)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                print(f"✅ {test_name}: PASSED")
                results.append((test_name, "PASSED", ""))
            else:
                print(f"❌ {test_name}: FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                results.append((test_name, "FAILED", result.stderr))
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name}: TIMEOUT")
            results.append((test_name, "TIMEOUT", "Test exceeded 5 minute limit"))
            
        except FileNotFoundError:
            print(f"⚠️  {test_name}: SKIPPED (tool not found)")
            results.append((test_name, "SKIPPED", "Tool not available"))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")
    skipped = sum(1 for _, status, _ in results if status == "SKIPPED")
    timeout = sum(1 for _, status, _ in results if status == "TIMEOUT")
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Skipped: {skipped}")
    print(f"⏰ Timeout: {timeout}")
    
    if failed > 0 or timeout > 0:
        print("\n🚨 FAILED TESTS:")
        for test_name, status, error in results:
            if status in ["FAILED", "TIMEOUT"]:
                print(f"  - {test_name}: {status}")
                if error:
                    print(f"    Error: {error[:100]}...")
    
    # Overall result
    if failed == 0 and timeout == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {failed + timeout} TESTS FAILED")
        return False

def check_dependencies():
    """Check if all required testing dependencies are available"""
    
    print("🔍 Checking test dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-cov", 
        "pandas",
        "numpy"
    ]
    
    optional_packages = [
        "mypy",
        "flake8",
        "black"
    ]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}: Available")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package}: Missing (REQUIRED)")
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}: Available")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package}: Missing (optional)")
    
    if missing_required:
        print(f"\n🚨 Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n💡 Optional packages not available: {', '.join(missing_optional)}")
        print("Some tests may be skipped")
    
    return True

def main():
    """Main test runner"""
    
    print("YouTube EV Lead Generation Pipeline - Test Suite")
    print("Version: 1.0.0 (Optimized)")
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    # Run tests
    success = run_tests()
    
    if success:
        print("\n🚀 Ready for deployment!")
        sys.exit(0)
    else:
        print("\n🔧 Please fix failing tests before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
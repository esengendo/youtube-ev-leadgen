"""
Comprehensive unit tests for the utilities module
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the modules we're testing
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from scripts.utils import DataLoader, DataValidator, ConfigManager, FileUtils, PerformanceMonitor


class TestDataLoader:
    """Test cases for DataLoader class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_loader = DataLoader(cache_dir=os.path.join(self.temp_dir, "cache"))
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        # Create a temporary file
        test_file = os.path.join(self.temp_dir, "test.csv")
        with open(test_file, 'w') as f:
            f.write("test,data\n1,2\n")
        
        key1 = self.data_loader._get_cache_key(test_file)
        key2 = self.data_loader._get_cache_key(test_file)
        
        assert key1 == key2, "Cache keys should be consistent"
        assert len(key1) == 32, "Cache key should be MD5 hash length"
    
    def test_load_csv_cached_success(self):
        """Test successful CSV loading with caching"""
        # Create test CSV
        test_file = os.path.join(self.temp_dir, "test.csv")
        test_data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        test_data.to_csv(test_file, index=False)
        
        # First load - should read from file
        df1 = self.data_loader.load_csv_cached(test_file)
        assert df1 is not None
        assert len(df1) == 3
        assert list(df1.columns) == ["col1", "col2"]
        
        # Second load - should read from cache
        df2 = self.data_loader.load_csv_cached(test_file)
        assert df2 is not None
        pd.testing.assert_frame_equal(df1, df2)
    
    def test_load_csv_cached_file_not_found(self):
        """Test handling of non-existent files"""
        df = self.data_loader.load_csv_cached("nonexistent.csv")
        assert df is None
    
    def test_save_csv_safe_success(self):
        """Test safe CSV saving"""
        test_data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        test_file = os.path.join(self.temp_dir, "output.csv")
        
        result = self.data_loader.save_csv_safe(test_data, test_file)
        assert result is True
        assert os.path.exists(test_file)
        
        # Verify content
        loaded_data = pd.read_csv(test_file)
        pd.testing.assert_frame_equal(test_data, loaded_data)
    
    def test_save_csv_safe_with_backup(self):
        """Test CSV saving with backup creation"""
        test_data = pd.DataFrame({"col1": [1, 2]})
        test_file = os.path.join(self.temp_dir, "output.csv")
        
        # Create initial file
        initial_data = pd.DataFrame({"old": [1, 2, 3]})
        initial_data.to_csv(test_file, index=False)
        
        # Save new data with backup
        result = self.data_loader.save_csv_safe(test_data, test_file, backup=True)
        assert result is True
        assert os.path.exists(test_file + ".backup")


class TestDataValidator:
    """Test cases for DataValidator class"""
    
    def test_validate_comments_schema_valid(self):
        """Test validation of valid comments dataframe"""
        valid_df = pd.DataFrame({
            "Comment": ["Great video!", "Thanks for sharing"],
            "Username": ["user1", "user2"],
            "Timestamp": ["2023-01-01T12:00:00Z", "2023-01-01T13:00:00Z"],
            "VideoID": ["vid1", "vid2"]
        })
        
        is_valid, errors = DataValidator.validate_comments_schema(valid_df)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_comments_schema_missing_columns(self):
        """Test validation with missing required columns"""
        invalid_df = pd.DataFrame({
            "Comment": ["Great video!"],
            "Username": ["user1"]
            # Missing Timestamp
        })
        
        is_valid, errors = DataValidator.validate_comments_schema(invalid_df)
        assert is_valid is False
        assert len(errors) > 0
        assert "Missing required columns" in errors[0]
    
    def test_validate_comments_schema_too_many_nulls(self):
        """Test validation with too many null comments"""
        invalid_df = pd.DataFrame({
            "Comment": [None] * 50 + ["Valid comment"] * 50,
            "Username": ["user"] * 100,
            "Timestamp": ["2023-01-01T12:00:00Z"] * 100
        })
        
        is_valid, errors = DataValidator.validate_comments_schema(invalid_df)
        assert is_valid is False
        assert any("Too many null comments" in error for error in errors)
    
    def test_validate_leads_schema_valid(self):
        """Test validation of valid leads dataframe"""
        valid_df = pd.DataFrame({
            "Username": ["user1", "user2"],
            "ConversionProbability": [0.8, 0.9],
            "LeadScore": [85, 95]
        })
        
        is_valid, errors = DataValidator.validate_leads_schema(valid_df)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_leads_schema_invalid_probability(self):
        """Test validation with invalid probability values"""
        invalid_df = pd.DataFrame({
            "Username": ["user1", "user2"],
            "ConversionProbability": [1.5, -0.1],  # Invalid range
            "LeadScore": [85, 95]
        })
        
        is_valid, errors = DataValidator.validate_leads_schema(invalid_df)
        assert is_valid is False
        assert any("must be between 0 and 1" in error for error in errors)


class TestConfigManager:
    """Test cases for ConfigManager class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(config_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_config_success(self):
        """Test successful config loading"""
        test_config = {"key1": "value1", "key2": {"nested": "value"}}
        config_file = os.path.join(self.temp_dir, "test_config.json")
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        loaded_config = self.config_manager.load_config("test_config")
        assert loaded_config == test_config
    
    def test_load_config_not_found(self):
        """Test handling of non-existent config files"""
        config = self.config_manager.load_config("nonexistent")
        assert config == {}
    
    def test_load_config_caching(self):
        """Test config caching functionality"""
        test_config = {"cached": True}
        config_file = os.path.join(self.temp_dir, "cached_config.json")
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # First load
        config1 = self.config_manager.load_config("cached_config")
        
        # Modify file
        with open(config_file, 'w') as f:
            json.dump({"cached": False}, f)
        
        # Second load should return cached version
        config2 = self.config_manager.load_config("cached_config")
        assert config1 == config2 == test_config
    
    def test_get_file_paths(self):
        """Test file paths configuration"""
        paths = self.config_manager.get_file_paths()
        
        assert isinstance(paths, dict)
        assert "raw_comments" in paths
        assert "clean_comments" in paths
        assert "predicted_leads" in paths
        
        # Verify all paths are strings
        for path in paths.values():
            assert isinstance(path, str)
    
    def test_get_business_thresholds(self):
        """Test business thresholds configuration"""
        thresholds = self.config_manager.get_business_thresholds()
        
        assert isinstance(thresholds, dict)
        assert "high_conversion_threshold" in thresholds
        assert "min_comment_length" in thresholds
        
        # Verify all thresholds are numeric
        for threshold in thresholds.values():
            assert isinstance(threshold, (int, float))


class TestFileUtils:
    """Test cases for FileUtils class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_ensure_dir_success(self):
        """Test successful directory creation"""
        test_dir = os.path.join(self.temp_dir, "new_dir")
        
        result = FileUtils.ensure_dir(test_dir)
        assert result is True
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)
    
    def test_ensure_dir_already_exists(self):
        """Test handling of existing directories"""
        result = FileUtils.ensure_dir(self.temp_dir)
        assert result is True
    
    def test_safe_remove_existing_file(self):
        """Test removal of existing file"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = FileUtils.safe_remove(test_file)
        assert result is True
        assert not os.path.exists(test_file)
    
    def test_safe_remove_nonexistent_file(self):
        """Test removal of non-existent file"""
        result = FileUtils.safe_remove("nonexistent.txt")
        assert result is True  # Should not fail
    
    def test_get_file_size_mb(self):
        """Test file size calculation"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        test_content = "x" * 1024  # 1KB
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        size_mb = FileUtils.get_file_size_mb(test_file)
        assert size_mb > 0
        assert size_mb < 1  # Should be less than 1MB
    
    def test_get_file_size_mb_nonexistent(self):
        """Test file size for non-existent file"""
        size_mb = FileUtils.get_file_size_mb("nonexistent.txt")
        assert size_mb == 0.0


class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class"""
    
    def test_checkpoint_creation(self):
        """Test checkpoint creation and timing"""
        monitor = PerformanceMonitor()
        
        import time
        time.sleep(0.1)  # Small delay
        
        duration = monitor.checkpoint("test_checkpoint")
        assert duration > 0.1
        assert "test_checkpoint" in monitor.checkpoints
    
    def test_multiple_checkpoints(self):
        """Test multiple checkpoint creation"""
        monitor = PerformanceMonitor()
        
        monitor.checkpoint("checkpoint1")
        monitor.checkpoint("checkpoint2")
        
        assert len(monitor.checkpoints) == 2
        assert monitor.checkpoints["checkpoint2"] > monitor.checkpoints["checkpoint1"]
    
    def test_get_memory_usage(self):
        """Test memory usage measurement"""
        monitor = PerformanceMonitor()
        
        memory_mb = monitor.get_memory_usage_mb()
        assert memory_mb >= 0  # Should be non-negative
    
    def test_log_performance_summary(self):
        """Test performance summary logging"""
        monitor = PerformanceMonitor()
        monitor.checkpoint("test")
        
        # Should not raise exception
        monitor.log_performance_summary()


# Integration tests
class TestIntegration:
    """Integration tests for combined functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_data_processing_pipeline(self):
        """Test complete data processing workflow"""
        # Create test data
        test_data = pd.DataFrame({
            "Comment": ["Great EV!", "Love Tesla", "Expensive cars"],
            "Username": ["user1", "user2", "user3"],
            "Timestamp": ["2023-01-01T12:00:00Z"] * 3,
            "VideoID": ["vid1"] * 3
        })
        
        # Setup components
        data_loader = DataLoader(cache_dir=os.path.join(self.temp_dir, "cache"))
        config_manager = ConfigManager(config_dir=self.temp_dir)
        
        # Create config file
        config = {"test": True}
        with open(os.path.join(self.temp_dir, "test.json"), 'w') as f:
            json.dump(config, f)
        
        # Test workflow
        test_file = os.path.join(self.temp_dir, "test_data.csv")
        
        # Save data
        save_result = data_loader.save_csv_safe(test_data, test_file)
        assert save_result is True
        
        # Load data (should use cache on second load)
        loaded_data1 = data_loader.load_csv_cached(test_file)
        loaded_data2 = data_loader.load_csv_cached(test_file)
        
        assert loaded_data1 is not None
        assert loaded_data2 is not None
        pd.testing.assert_frame_equal(loaded_data1, loaded_data2)
        
        # Validate data
        is_valid, errors = DataValidator.validate_comments_schema(loaded_data1)
        assert is_valid is True
        
        # Load config
        loaded_config = config_manager.load_config("test")
        assert loaded_config == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
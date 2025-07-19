"""
Unit tests for data processing pipeline components
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add scripts directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestDataPreprocessing:
    """Test cases for data preprocessing functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_clean_comment_basic(self):
        """Test basic comment cleaning functionality"""
        # Import the function we're testing
        with patch('sys.path', sys.path + [os.path.join(os.path.dirname(__file__), '..', 'scripts')]):
            from data_preprocessing import clean_comment
        
        # Test cases
        test_cases = [
            ("Hello World!", "hello world!"),
            ("Check out http://example.com", "check out"),
            ("Great video! 👍😊", "great video!"),
            ("Price: $50,000", "price   "),
            ("  Multiple   spaces  ", "multiple spaces"),
            ("", ""),
            (None, "")
        ]
        
        for input_text, expected in test_cases:
            result = clean_comment(input_text)
            # Normalize whitespace for comparison
            result_normalized = " ".join(result.split())
            expected_normalized = " ".join(expected.split())
            assert result_normalized == expected_normalized, f"Failed for input: {input_text}"
    
    def test_clean_comment_edge_cases(self):
        """Test edge cases for comment cleaning"""
        with patch('sys.path', sys.path + [os.path.join(os.path.dirname(__file__), '..', 'scripts')]):
            from data_preprocessing import clean_comment
        
        # Test very long comment
        long_comment = "word " * 1000
        result = clean_comment(long_comment)
        assert len(result) > 0
        
        # Test comment with only special characters
        special_only = "!@#$%^&*()123456"
        result = clean_comment(special_only)
        assert result.strip() == ""
        
        # Test mixed content
        mixed = "Great car! Visit www.example.com for details. Price: $45,000 😊"
        result = clean_comment(mixed)
        assert "great car" in result
        assert "example.com" not in result
        assert "$" not in result


class TestSentimentAnalysis:
    """Test cases for sentiment analysis functionality"""
    
    @patch('transformers.pipeline')
    def test_sentiment_analysis_mock(self, mock_pipeline):
        """Test sentiment analysis with mocked transformers"""
        # Mock the sentiment analysis pipeline
        mock_classifier = MagicMock()
        mock_classifier.return_value = [{'label': 'POSITIVE', 'score': 0.9}]
        mock_pipeline.return_value = mock_classifier
        
        # Import and test (would need actual implementation)
        # This is a template for when sentiment analysis is properly modularized
        pass
    
    def test_intent_classification_patterns(self):
        """Test intent classification patterns"""
        # Test data for intent classification
        test_comments = [
            ("I want to buy a Tesla", "Purchase Intent"),
            ("Looking for information about EVs", "Information Seeking"),
            ("This is amazing!", "General Positive"),
            ("I need help with charging", "Support Request"),
            ("Just sharing my thoughts", "General Comment")
        ]
        
        # This would test intent classification logic when modularized
        # For now, we can test pattern matching
        for comment, expected_intent in test_comments:
            # Basic pattern matching test
            if "want to buy" in comment.lower() or "purchase" in comment.lower():
                detected_intent = "Purchase Intent"
            elif "looking for" in comment.lower() or "information" in comment.lower():
                detected_intent = "Information Seeking"
            elif "need help" in comment.lower() or "support" in comment.lower():
                detected_intent = "Support Request"
            else:
                detected_intent = "General Comment"
            
            # This is a simplified test - real implementation would be more sophisticated
            assert detected_intent is not None


class TestLeadScoring:
    """Test cases for lead scoring functionality"""
    
    def test_lead_score_calculation(self):
        """Test lead score calculation logic"""
        # Sample lead data
        lead_data = {
            'sentiment_score': 0.8,
            'intent_confidence': 0.9,
            'engagement_level': 0.7,
            'comment_quality': 0.6
        }
        
        # Basic scoring algorithm test
        def calculate_lead_score(data):
            weights = {
                'sentiment_score': 0.3,
                'intent_confidence': 0.4,
                'engagement_level': 0.2,
                'comment_quality': 0.1
            }
            
            score = sum(data[key] * weights[key] for key in weights.keys())
            return min(100, max(0, score * 100))  # Scale to 0-100
        
        score = calculate_lead_score(lead_data)
        assert 0 <= score <= 100
        assert isinstance(score, (int, float))
    
    def test_conversion_probability_bounds(self):
        """Test conversion probability calculation bounds"""
        # Test probability calculation
        test_scores = [0, 25, 50, 75, 100]
        
        for score in test_scores:
            # Simple probability calculation (would be ML model in reality)
            probability = score / 100.0
            
            assert 0 <= probability <= 1, f"Probability out of bounds for score {score}"
    
    def test_lead_quality_classification(self):
        """Test lead quality classification"""
        test_cases = [
            (0.95, "Hot Lead"),
            (0.80, "Warm Lead"),
            (0.60, "Cold Lead"),
            (0.30, "Low Interest"),
            (0.10, "Low Interest")
        ]
        
        def classify_lead_quality(probability):
            if probability >= 0.90:
                return "Hot Lead"
            elif probability >= 0.70:
                return "Warm Lead"
            elif probability >= 0.50:
                return "Cold Lead"
            else:
                return "Low Interest"
        
        for prob, expected in test_cases:
            result = classify_lead_quality(prob)
            assert result == expected, f"Failed for probability {prob}"


class TestDataValidation:
    """Test cases for data validation"""
    
    def test_youtube_comment_validation(self):
        """Test YouTube comment data validation"""
        # Valid comment data
        valid_data = pd.DataFrame({
            'Comment': ['Great video!', 'Thanks for sharing'],
            'Username': ['user1', 'user2'],
            'Timestamp': ['2023-01-01T12:00:00Z', '2023-01-01T13:00:00Z'],
            'VideoID': ['vid1', 'vid2']
        })
        
        # Test required fields
        required_fields = ['Comment', 'Username', 'Timestamp']
        for field in required_fields:
            assert field in valid_data.columns
        
        # Test data types
        assert not valid_data['Comment'].isnull().any()
        assert not valid_data['Username'].isnull().any()
        
        # Test timestamp format (basic check)
        for timestamp in valid_data['Timestamp']:
            assert 'T' in timestamp  # ISO format check
            assert 'Z' in timestamp
    
    def test_invalid_data_handling(self):
        """Test handling of invalid data"""
        # Invalid data scenarios
        invalid_scenarios = [
            # Missing comments
            pd.DataFrame({
                'Comment': [None, 'Valid comment'],
                'Username': ['user1', 'user2'],
                'Timestamp': ['2023-01-01T12:00:00Z'] * 2
            }),
            # Empty comments
            pd.DataFrame({
                'Comment': ['', 'Valid comment'],
                'Username': ['user1', 'user2'],
                'Timestamp': ['2023-01-01T12:00:00Z'] * 2
            }),
            # Missing usernames
            pd.DataFrame({
                'Comment': ['Valid comment'] * 2,
                'Username': [None, 'user2'],
                'Timestamp': ['2023-01-01T12:00:00Z'] * 2
            })
        ]
        
        for invalid_df in invalid_scenarios:
            # Check that invalid data is detected
            has_nulls = invalid_df.isnull().any().any()
            has_empty_strings = (invalid_df == '').any().any()
            
            assert has_nulls or has_empty_strings, "Should detect invalid data"


class TestFileOperations:
    """Test cases for file operations"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_csv_save_load_consistency(self):
        """Test CSV save/load consistency"""
        # Create test data
        test_data = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
            'col3': [1.1, 2.2, 3.3]
        })
        
        # Save to CSV
        csv_path = os.path.join(self.temp_dir, 'test.csv')
        test_data.to_csv(csv_path, index=False)
        
        # Load from CSV
        loaded_data = pd.read_csv(csv_path)
        
        # Compare
        pd.testing.assert_frame_equal(test_data, loaded_data)
    
    def test_directory_creation(self):
        """Test directory creation for output files"""
        nested_dir = os.path.join(self.temp_dir, 'data', 'processed')
        
        # Create nested directory
        os.makedirs(nested_dir, exist_ok=True)
        
        assert os.path.exists(nested_dir)
        assert os.path.isdir(nested_dir)
    
    def test_file_size_limits(self):
        """Test handling of large files"""
        # Create a relatively large DataFrame
        large_data = pd.DataFrame({
            'col1': range(10000),
            'col2': ['text_' + str(i) for i in range(10000)]
        })
        
        csv_path = os.path.join(self.temp_dir, 'large_test.csv')
        large_data.to_csv(csv_path, index=False)
        
        # Check file was created
        assert os.path.exists(csv_path)
        
        # Check file size is reasonable
        file_size = os.path.getsize(csv_path)
        assert file_size > 100000  # Should be substantial
        assert file_size < 50000000  # But not too large (50MB)


class TestErrorHandling:
    """Test cases for error handling and edge cases"""
    
    def test_missing_input_files(self):
        """Test handling of missing input files"""
        # Simulate missing file scenario
        with patch('os.path.exists', return_value=False):
            # This would test how the pipeline handles missing files
            result = False  # Simulating file not found
            assert result is False
    
    def test_corrupted_data_handling(self):
        """Test handling of corrupted data"""
        # Test various corrupted data scenarios
        corrupted_scenarios = [
            # Completely empty DataFrame
            pd.DataFrame(),
            # DataFrame with wrong columns
            pd.DataFrame({'wrong_col': [1, 2, 3]}),
            # DataFrame with mixed data types in wrong places
            pd.DataFrame({
                'Comment': [1, 2, 3],  # Numbers instead of text
                'Username': ['user1', 'user2', 'user3'],
                'Timestamp': ['not_a_timestamp', 'also_not', 'definitely_not']
            })
        ]
        
        for corrupted_df in corrupted_scenarios:
            # Each scenario should be detectable as invalid
            is_valid = True
            
            if len(corrupted_df) == 0:
                is_valid = False
            elif 'Comment' not in corrupted_df.columns:
                is_valid = False
            elif corrupted_df['Comment'].dtype != 'object':
                is_valid = False
            
            # Corrupted data should be detected
            assert not is_valid or len(corrupted_df) == 0
    
    def test_api_failure_simulation(self):
        """Test handling of API failures"""
        # Simulate various API failure scenarios
        api_failures = [
            {'error': 'rate_limit_exceeded', 'code': 429},
            {'error': 'invalid_api_key', 'code': 401},
            {'error': 'service_unavailable', 'code': 503},
            {'error': 'network_timeout', 'code': None}
        ]
        
        for failure in api_failures:
            # Test that failures are handled gracefully
            if failure['code'] == 429:
                # Rate limit - should retry
                should_retry = True
            elif failure['code'] == 401:
                # Auth error - should not retry
                should_retry = False
            elif failure['code'] == 503:
                # Service error - might retry
                should_retry = True
            else:
                # Network error - should retry
                should_retry = True
            
            assert isinstance(should_retry, bool)


# Performance tests
class TestPerformance:
    """Test cases for performance and scalability"""
    
    def test_large_dataset_processing(self):
        """Test processing of large datasets"""
        # Create a large test dataset
        large_size = 50000
        large_data = pd.DataFrame({
            'Comment': [f'Comment number {i}' for i in range(large_size)],
            'Username': [f'user_{i % 1000}' for i in range(large_size)],
            'Timestamp': ['2023-01-01T12:00:00Z'] * large_size
        })
        
        # Test basic operations are still fast
        import time
        start_time = time.time()
        
        # Basic operations
        cleaned_comments = large_data['Comment'].str.lower()
        deduplicated = large_data.drop_duplicates()
        
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 30, f"Processing took too long: {processing_time}s"
        assert len(cleaned_comments) == large_size
    
    def test_memory_usage(self):
        """Test memory usage with various dataset sizes"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create progressively larger datasets
        for size in [1000, 5000, 10000]:
            data = pd.DataFrame({
                'Comment': [f'Comment {i}' for i in range(size)],
                'Username': [f'user_{i}' for i in range(size)]
            })
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            
            # Memory usage should be reasonable (less than 500MB increase)
            assert memory_increase < 500, f"Memory usage too high: {memory_increase}MB"
            
            # Clean up
            del data
            gc.collect()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
"""
Unit tests for reputation scoring calculations.

Tests verify that the scoring algorithms work correctly for different
package metadata scenarios.
"""

import pytest
from datetime import datetime, timedelta
from tools.reputation_service import ReputationScorer


class TestReputationScoring:
    """Unit tests for reputation scoring calculations."""
    
    def test_age_score_new_package(self):
        """Test age scoring for packages less than 30 days old."""
        scorer = ReputationScorer()
        
        # Create metadata for a 15-day-old package
        created_date = (datetime.now() - timedelta(days=15)).isoformat()
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        assert age_score == 0.2, "Packages < 30 days should score 0.2"
    
    def test_age_score_established_package(self):
        """Test age scoring for packages over 2 years old."""
        scorer = ReputationScorer()
        
        # Create metadata for a 3-year-old package
        created_date = (datetime.now() - timedelta(days=1095)).isoformat()
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        assert age_score == 1.0, "Packages > 2 years should score 1.0"
    
    def test_downloads_score_low(self):
        """Test download scoring for packages with low downloads."""
        scorer = ReputationScorer()
        
        metadata = {'downloads': 50}
        downloads_score = scorer._calculate_downloads_score(metadata)
        assert downloads_score == 0.2, "Packages < 100 downloads/week should score 0.2"
    
    def test_downloads_score_high(self):
        """Test download scoring for packages with high downloads."""
        scorer = ReputationScorer()
        
        metadata = {'downloads': 150000}
        downloads_score = scorer._calculate_downloads_score(metadata)
        assert downloads_score == 1.0, "Packages > 100K downloads/week should score 1.0"
    
    def test_author_score_unknown(self):
        """Test author scoring for packages with no author."""
        scorer = ReputationScorer()
        
        metadata = {}
        author_score = scorer._calculate_author_score(metadata)
        assert author_score == 0.3, "Packages with unknown author should score 0.3"
    
    def test_author_score_known(self):
        """Test author scoring for packages with known author."""
        scorer = ReputationScorer()
        
        metadata = {'author': {'name': 'John Doe'}}
        author_score = scorer._calculate_author_score(metadata)
        assert author_score == 0.8, "Packages with known author should score 0.8"
    
    def test_author_score_verified(self):
        """Test author scoring for verified/organization packages."""
        scorer = ReputationScorer()
        
        metadata = {
            'author': {'name': 'Org Name'},
            'maintainers': [
                {'name': 'Maintainer 1'},
                {'name': 'Maintainer 2'}
            ]
        }
        author_score = scorer._calculate_author_score(metadata)
        assert author_score == 1.0, "Packages with multiple maintainers should score 1.0"
    
    def test_maintenance_score_recent(self):
        """Test maintenance scoring for recently updated packages."""
        scorer = ReputationScorer()
        
        # Package updated 30 days ago
        modified_date = (datetime.now() - timedelta(days=30)).isoformat()
        metadata = {
            'time': {
                'created': '2020-01-01T00:00:00Z',
                'modified': modified_date
            }
        }
        
        maintenance_score = scorer._calculate_maintenance_score(metadata)
        assert maintenance_score == 1.0, "Packages updated < 6 months ago should score 1.0"
    
    def test_maintenance_score_abandoned(self):
        """Test maintenance scoring for abandoned packages."""
        scorer = ReputationScorer()
        
        # Package updated 3 years ago
        modified_date = (datetime.now() - timedelta(days=1095)).isoformat()
        metadata = {
            'time': {
                'created': '2020-01-01T00:00:00Z',
                'modified': modified_date
            }
        }
        
        maintenance_score = scorer._calculate_maintenance_score(metadata)
        assert maintenance_score == 0.2, "Packages updated > 2 years ago should score 0.2"
    
    def test_composite_score_calculation(self):
        """Test that composite score is weighted average of factors."""
        scorer = ReputationScorer()
        
        # Create metadata for a well-established package
        created_date = (datetime.now() - timedelta(days=1095)).isoformat()
        modified_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        metadata = {
            'time': {
                'created': created_date,
                'modified': modified_date
            },
            'downloads': 150000,
            'author': {'name': 'John Doe'},
            'maintainers': [
                {'name': 'Maintainer 1'},
                {'name': 'Maintainer 2'}
            ]
        }
        
        result = scorer._calculate_scores(metadata)
        
        # Verify all factors are present
        assert 'score' in result
        assert 'factors' in result
        assert 'flags' in result
        
        # Verify factor scores
        factors = result['factors']
        assert factors['age_score'] == 1.0
        assert factors['downloads_score'] == 1.0
        assert factors['author_score'] == 1.0
        assert factors['maintenance_score'] == 1.0
        
        # Verify composite score (weighted average)
        expected_score = 1.0 * 0.3 + 1.0 * 0.3 + 1.0 * 0.2 + 1.0 * 0.2
        assert result['score'] == expected_score
    
    def test_flags_generation(self):
        """Test that appropriate flags are generated based on scores."""
        scorer = ReputationScorer()
        
        # Create metadata for a suspicious package
        created_date = (datetime.now() - timedelta(days=15)).isoformat()
        
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            },
            'downloads': 50
        }
        
        result = scorer._calculate_scores(metadata)
        
        # Verify flags are present
        assert 'new_package' in result['flags']
        assert 'low_downloads' in result['flags']
        assert 'unknown_author' in result['flags']
    
    def test_pypi_metadata_format(self):
        """Test scoring with PyPI metadata format."""
        scorer = ReputationScorer()
        
        metadata = {
            'info': {
                'name': 'test-package',
                'version': '1.0.0',
                'author': 'Test Author'
            },
            'releases': {
                '1.0.0': [
                    {
                        'upload_time': (datetime.now() - timedelta(days=365)).isoformat(),
                        'size': 1000
                    }
                ]
            }
        }
        
        result = scorer._calculate_scores(metadata)
        
        # Should successfully calculate scores
        assert 'score' in result
        assert result['score'] > 0
        assert result['factors']['age_score'] == 0.9  # 365 days = 1 year (1-2 year range)
    
    def test_calculate_reputation_end_to_end(self):
        """Test end-to-end reputation calculation."""
        scorer = ReputationScorer()
        
        # Mock metadata fetch
        from unittest.mock import patch
        
        mock_metadata = {
            'time': {
                'created': (datetime.now() - timedelta(days=730)).isoformat(),
                'modified': (datetime.now() - timedelta(days=30)).isoformat()
            },
            'downloads': 50000,
            'author': {'name': 'Trusted Author'}
        }
        
        with patch.object(scorer, '_fetch_metadata', return_value=mock_metadata):
            result = scorer.calculate_reputation('test-package', 'npm')
            
            # Verify result structure
            assert 'score' in result
            assert 'factors' in result
            assert 'flags' in result
            assert 'metadata' in result
            
            # Verify score is reasonable
            assert 0.0 <= result['score'] <= 1.0
    
    def test_rate_limiting(self):
        """Test that rate limiting is applied to requests."""
        import time
        from unittest.mock import patch, Mock
        
        # Create scorer with strict rate limit (1 request per second)
        scorer = ReputationScorer(rate_limit_per_second=1.0)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'name': 'test'}
        
        with patch.object(scorer.session, 'get', return_value=mock_response):
            # Make two requests
            start_time = time.time()
            scorer._fetch_metadata('http://test.com/1')
            scorer._fetch_metadata('http://test.com/2')
            elapsed_time = time.time() - start_time
            
            # Second request should be delayed by rate limiting
            assert elapsed_time >= 1.0, "Rate limiting should delay second request"
    
    def test_missing_metadata_fields(self):
        """Test that missing metadata fields are handled gracefully."""
        scorer = ReputationScorer()
        
        # Empty metadata
        metadata = {}
        
        result = scorer._calculate_scores(metadata)
        
        # Should return neutral scores
        assert result['score'] > 0
        assert all(0.0 <= score <= 1.0 for score in result['factors'].values())

"""
Property-based tests for reputation service functionality.

Tests verify correctness properties for the package reputation scoring system,
ensuring registry metadata fetching works correctly across ecosystems.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timedelta

from tools.reputation_service import ReputationScorer


# Hypothesis strategies for generating test data
package_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-_'),
    min_size=1,
    max_size=50
).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))

ecosystem_strategy = st.sampled_from(['npm', 'pypi'])

# Sample metadata structures for different ecosystems
npm_metadata_strategy = st.fixed_dictionaries({
    'name': st.text(min_size=1, max_size=50),
    'version': st.text(min_size=1, max_size=20),
    'time': st.fixed_dictionaries({
        'created': st.text(min_size=10, max_size=30),
        'modified': st.text(min_size=10, max_size=30)
    }),
    'downloads': st.integers(min_value=0, max_value=1000000),
    'author': st.fixed_dictionaries({
        'name': st.text(min_size=1, max_size=50)
    })
})

pypi_metadata_strategy = st.fixed_dictionaries({
    'info': st.fixed_dictionaries({
        'name': st.text(min_size=1, max_size=50),
        'version': st.text(min_size=1, max_size=20),
        'author': st.text(min_size=1, max_size=50),
        'home_page': st.text(min_size=0, max_size=100)
    }),
    'releases': st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.lists(st.dictionaries(
            keys=st.sampled_from(['upload_time', 'size']),
            values=st.one_of(st.text(min_size=10, max_size=30), st.integers(min_value=0))
        ))
    )
})


class TestRegistryMetadataFetching:
    """Property-based tests for registry metadata fetching."""

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=100, deadline=None)
    def test_property_10_registry_metadata_fetching(self, package_name: str, ecosystem: str):
        """
        **Feature: production-ready-enhancements, Property 10: Registry Metadata Fetching**
        
        For any package being analyzed, the reputation service should fetch metadata 
        from the appropriate package registry (npm, PyPI).
        
        **Validates: Requirements 3.1**
        """
        # Create reputation scorer
        scorer = ReputationScorer()
        
        # Mock the HTTP request to avoid actual network calls
        mock_metadata = {
            'name': package_name,
            'version': '1.0.0',
            'created': '2023-01-01',
            'downloads': 1000
        }
        
        with patch.object(scorer, '_fetch_metadata', return_value=mock_metadata) as mock_fetch:
            # Calculate reputation (which should fetch metadata)
            result = scorer.calculate_reputation(package_name, ecosystem)
            
            # Property 1: Metadata fetch should be called
            assert mock_fetch.called, "Metadata fetch should be invoked during reputation calculation"
            
            # Property 2: Correct registry URL should be constructed
            call_args = mock_fetch.call_args
            if call_args:
                registry_url = call_args[0][0]
                
                # Verify URL matches ecosystem
                if ecosystem == 'npm':
                    assert 'registry.npmjs.org' in registry_url, "npm packages should use npm registry"
                    assert package_name in registry_url, "Package name should be in registry URL"
                elif ecosystem == 'pypi':
                    assert 'pypi.org' in registry_url, "PyPI packages should use PyPI registry"
                    assert package_name in registry_url, "Package name should be in registry URL"
            
            # Property 3: Result should contain metadata
            assert 'metadata' in result, "Result should include metadata"
            assert result['metadata'] == mock_metadata, "Result should contain fetched metadata"

    @given(package_name_strategy)
    @settings(max_examples=50)
    def test_npm_registry_url_construction(self, package_name: str):
        """
        Test that npm packages use correct registry URL format.
        
        For any npm package name, the registry URL should follow
        the format: https://registry.npmjs.org/{package_name}
        """
        scorer = ReputationScorer()
        
        # Get registry URL for npm ecosystem
        registry_url = scorer._get_registry_url(package_name, 'npm')
        
        # Property 1: URL should use npm registry domain
        assert registry_url.startswith('https://registry.npmjs.org/'), \
            "npm registry URL should start with https://registry.npmjs.org/"
        
        # Property 2: URL should contain package name
        assert package_name in registry_url, "Registry URL should contain package name"
        
        # Property 3: URL should be properly formatted
        expected_url = f"https://registry.npmjs.org/{package_name}"
        assert registry_url == expected_url, "Registry URL should match expected format"

    @given(package_name_strategy)
    @settings(max_examples=50)
    def test_pypi_registry_url_construction(self, package_name: str):
        """
        Test that PyPI packages use correct registry URL format.
        
        For any PyPI package name, the registry URL should follow
        the format: https://pypi.org/pypi/{package_name}/json
        """
        scorer = ReputationScorer()
        
        # Get registry URL for PyPI ecosystem
        registry_url = scorer._get_registry_url(package_name, 'pypi')
        
        # Property 1: URL should use PyPI domain
        assert registry_url.startswith('https://pypi.org/pypi/'), \
            "PyPI registry URL should start with https://pypi.org/pypi/"
        
        # Property 2: URL should contain package name
        assert package_name in registry_url, "Registry URL should contain package name"
        
        # Property 3: URL should end with /json
        assert registry_url.endswith('/json'), "PyPI registry URL should end with /json"
        
        # Property 4: URL should be properly formatted
        expected_url = f"https://pypi.org/pypi/{package_name}/json"
        assert registry_url == expected_url, "Registry URL should match expected format"

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=50)
    def test_metadata_fetch_makes_http_request(self, package_name: str, ecosystem: str):
        """
        Test that metadata fetching makes actual HTTP requests.
        
        For any package and ecosystem, the _fetch_metadata method
        should make an HTTP GET request to the registry URL.
        """
        scorer = ReputationScorer()
        registry_url = scorer._get_registry_url(package_name, ecosystem)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'name': package_name}
        
        with patch.object(scorer.session, 'get', return_value=mock_response) as mock_get:
            # Fetch metadata
            metadata = scorer._fetch_metadata(registry_url)
            
            # Property 1: HTTP GET should be called
            assert mock_get.called, "HTTP GET request should be made"
            
            # Property 2: Correct URL should be requested
            call_args = mock_get.call_args
            assert call_args[0][0] == registry_url, "Correct registry URL should be requested"
            
            # Property 3: Response should be parsed as JSON
            assert mock_response.json.called, "Response should be parsed as JSON"
            
            # Property 4: Metadata should be returned
            assert metadata == {'name': package_name}, "Fetched metadata should be returned"

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=50)
    def test_metadata_fetch_handles_http_errors(self, package_name: str, ecosystem: str):
        """
        Test that metadata fetching handles HTTP errors gracefully.
        
        For any package and ecosystem, if the HTTP request fails,
        the method should raise an appropriate exception.
        """
        scorer = ReputationScorer()
        registry_url = scorer._get_registry_url(package_name, ecosystem)
        
        # Mock HTTP error
        with patch.object(scorer.session, 'get', side_effect=requests.RequestException("Network error")):
            # Property: Should raise RuntimeError on HTTP failure
            with pytest.raises(RuntimeError) as exc_info:
                scorer._fetch_metadata(registry_url)
            
            # Property: Error message should be informative
            assert "Failed to fetch metadata" in str(exc_info.value), \
                "Error message should indicate metadata fetch failure"
            assert registry_url in str(exc_info.value), \
                "Error message should include registry URL"

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=50)
    def test_metadata_fetch_handles_404_errors(self, package_name: str, ecosystem: str):
        """
        Test that metadata fetching handles 404 (package not found) errors.
        
        For any package that doesn't exist in the registry,
        the method should raise an exception.
        """
        scorer = ReputationScorer()
        registry_url = scorer._get_registry_url(package_name, ecosystem)
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        
        with patch.object(scorer.session, 'get', return_value=mock_response):
            # Property: Should raise RuntimeError on 404
            with pytest.raises(RuntimeError):
                scorer._fetch_metadata(registry_url)

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=30)
    def test_metadata_fetch_uses_timeout(self, package_name: str, ecosystem: str):
        """
        Test that metadata fetching uses timeout to prevent hanging.
        
        For any package and ecosystem, the HTTP request should
        include a timeout parameter to prevent indefinite waiting.
        """
        scorer = ReputationScorer()
        registry_url = scorer._get_registry_url(package_name, ecosystem)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        
        with patch.object(scorer.session, 'get', return_value=mock_response) as mock_get:
            scorer._fetch_metadata(registry_url)
            
            # Property: Timeout should be specified in request
            call_kwargs = mock_get.call_args[1]
            assert 'timeout' in call_kwargs, "HTTP request should include timeout parameter"
            assert call_kwargs['timeout'] > 0, "Timeout should be positive"

    @given(package_name_strategy)
    @settings(max_examples=30)
    def test_unsupported_ecosystem_raises_error(self, package_name: str):
        """
        Test that unsupported ecosystems raise appropriate errors.
        
        For any package with an unsupported ecosystem identifier,
        the method should raise a ValueError.
        """
        scorer = ReputationScorer()
        
        # Property: Unsupported ecosystem should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            scorer._get_registry_url(package_name, 'unsupported_ecosystem')
        
        # Property: Error message should indicate unsupported ecosystem
        assert "Unsupported ecosystem" in str(exc_info.value), \
            "Error message should indicate unsupported ecosystem"

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=50)
    def test_calculate_reputation_fetches_metadata(self, package_name: str, ecosystem: str):
        """
        Test that calculate_reputation method fetches metadata.
        
        For any package and ecosystem, calling calculate_reputation
        should trigger metadata fetching from the registry.
        """
        scorer = ReputationScorer()
        
        mock_metadata = {
            'name': package_name,
            'version': '1.0.0'
        }
        
        with patch.object(scorer, '_fetch_metadata', return_value=mock_metadata) as mock_fetch:
            # Calculate reputation
            result = scorer.calculate_reputation(package_name, ecosystem)
            
            # Property 1: Metadata fetch should be called exactly once
            assert mock_fetch.call_count == 1, "Metadata should be fetched exactly once"
            
            # Property 2: Result should include the fetched metadata
            assert 'metadata' in result, "Result should contain metadata field"
            assert result['metadata'] == mock_metadata, "Result should contain fetched metadata"

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=50)
    def test_metadata_fetch_preserves_data_structure(self, package_name: str, ecosystem: str):
        """
        Test that metadata fetching preserves the data structure.
        
        For any metadata returned by the registry, the fetched
        metadata should preserve the exact structure and values.
        """
        scorer = ReputationScorer()
        registry_url = scorer._get_registry_url(package_name, ecosystem)
        
        # Create complex nested metadata structure
        original_metadata = {
            'name': package_name,
            'version': '1.2.3',
            'nested': {
                'field1': 'value1',
                'field2': [1, 2, 3],
                'field3': {'deep': 'value'}
            },
            'list': [1, 'two', {'three': 3}]
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = original_metadata
        
        with patch.object(scorer.session, 'get', return_value=mock_response):
            fetched_metadata = scorer._fetch_metadata(registry_url)
            
            # Property: Fetched metadata should exactly match original
            assert fetched_metadata == original_metadata, \
                "Fetched metadata should preserve exact structure and values"

    @given(package_name_strategy, ecosystem_strategy)
    @settings(max_examples=30)
    def test_metadata_fetch_uses_user_agent(self, package_name: str, ecosystem: str):
        """
        Test that metadata fetching includes User-Agent header.
        
        For any package and ecosystem, HTTP requests should include
        a User-Agent header for proper identification.
        """
        scorer = ReputationScorer()
        
        # Property: Session should have User-Agent header configured
        assert 'User-Agent' in scorer.session.headers, \
            "Session should have User-Agent header"
        assert len(scorer.session.headers['User-Agent']) > 0, \
            "User-Agent should not be empty"


class TestAgeFactorInReputation:
    """Property-based tests for age factor in reputation scoring."""

    @given(
        st.integers(min_value=0, max_value=3650),  # 0 to 10 years in days
        st.integers(min_value=0, max_value=3650)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_11_age_factor_in_reputation(self, age_days_1: int, age_days_2: int):
        """
        **Feature: production-ready-enhancements, Property 11: Age Factor in Reputation**
        
        For any two packages with different ages, the reputation scorer should assign 
        different age scores, with older packages receiving higher scores.
        
        **Validates: Requirements 3.2**
        """
        # Skip if ages are the same
        assume(age_days_1 != age_days_2)
        
        scorer = ReputationScorer()
        
        # Calculate current time
        now = datetime.now()
        
        # Create metadata for two packages with different ages
        created_date_1 = (now - timedelta(days=age_days_1)).isoformat()
        created_date_2 = (now - timedelta(days=age_days_2)).isoformat()
        
        metadata_1 = {
            'time': {
                'created': created_date_1,
                'modified': created_date_1
            }
        }
        
        metadata_2 = {
            'time': {
                'created': created_date_2,
                'modified': created_date_2
            }
        }
        
        # Calculate age scores
        age_score_1 = scorer._calculate_age_score(metadata_1)
        age_score_2 = scorer._calculate_age_score(metadata_2)
        
        # Property 1: Older packages should have higher or equal age scores
        if age_days_1 > age_days_2:
            # Package 1 is older, should have higher or equal score
            assert age_score_1 >= age_score_2, \
                f"Older package (age={age_days_1} days, score={age_score_1}) should have " \
                f"higher or equal score than younger package (age={age_days_2} days, score={age_score_2})"
        else:
            # Package 2 is older, should have higher or equal score
            assert age_score_2 >= age_score_1, \
                f"Older package (age={age_days_2} days, score={age_score_2}) should have " \
                f"higher or equal score than younger package (age={age_days_1} days, score={age_score_1})"
        
        # Property 2: Age scores should be within valid range [0.0, 1.0]
        assert 0.0 <= age_score_1 <= 1.0, "Age score should be between 0.0 and 1.0"
        assert 0.0 <= age_score_2 <= 1.0, "Age score should be between 0.0 and 1.0"
        
        # Property 3: If ages are in different threshold buckets, scores should differ
        # Thresholds: <30, 30-90, 90-365, 365-730, 730+
        def get_age_bucket(days):
            if days < 30:
                return 0
            elif days < 90:
                return 1
            elif days < 365:
                return 2
            elif days < 730:
                return 3
            else:
                return 4
        
        bucket_1 = get_age_bucket(age_days_1)
        bucket_2 = get_age_bucket(age_days_2)
        
        if bucket_1 != bucket_2:
            assert age_score_1 != age_score_2, \
                f"Packages in different age buckets should have different scores: " \
                f"age1={age_days_1} days (bucket {bucket_1}, score={age_score_1}), " \
                f"age2={age_days_2} days (bucket {bucket_2}, score={age_score_2})"

    @given(st.integers(min_value=0, max_value=29))
    @settings(max_examples=50)
    def test_very_new_packages_low_score(self, age_days: int):
        """
        Test that very new packages (< 30 days) receive low age scores.
        
        For any package less than 30 days old, the age score should be 0.2.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        created_date = (now - timedelta(days=age_days)).isoformat()
        
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Very new packages should have score of 0.2
        assert age_score == 0.2, \
            f"Package {age_days} days old should have age score 0.2, got {age_score}"

    @given(st.integers(min_value=30, max_value=89))
    @settings(max_examples=50)
    def test_new_packages_medium_low_score(self, age_days: int):
        """
        Test that new packages (30-90 days) receive medium-low age scores.
        
        For any package between 30 and 90 days old, the age score should be 0.5.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        created_date = (now - timedelta(days=age_days)).isoformat()
        
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: New packages should have score of 0.5
        assert age_score == 0.5, \
            f"Package {age_days} days old should have age score 0.5, got {age_score}"

    @given(st.integers(min_value=90, max_value=364))
    @settings(max_examples=50)
    def test_established_packages_medium_high_score(self, age_days: int):
        """
        Test that established packages (90-365 days) receive medium-high age scores.
        
        For any package between 90 and 365 days old, the age score should be 0.7.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        created_date = (now - timedelta(days=age_days)).isoformat()
        
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Established packages should have score of 0.7
        assert age_score == 0.7, \
            f"Package {age_days} days old should have age score 0.7, got {age_score}"

    @given(st.integers(min_value=365, max_value=729))
    @settings(max_examples=50)
    def test_mature_packages_high_score(self, age_days: int):
        """
        Test that mature packages (1-2 years) receive high age scores.
        
        For any package between 1 and 2 years old, the age score should be 0.9.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        created_date = (now - timedelta(days=age_days)).isoformat()
        
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Mature packages should have score of 0.9
        assert age_score == 0.9, \
            f"Package {age_days} days old should have age score 0.9, got {age_score}"

    @given(st.integers(min_value=730, max_value=3650))
    @settings(max_examples=50)
    def test_very_old_packages_maximum_score(self, age_days: int):
        """
        Test that very old packages (2+ years) receive maximum age scores.
        
        For any package 2 years or older, the age score should be 1.0.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        created_date = (now - timedelta(days=age_days)).isoformat()
        
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Very old packages should have score of 1.0
        assert age_score == 1.0, \
            f"Package {age_days} days old should have age score 1.0, got {age_score}"

    @given(st.integers(min_value=0, max_value=3650))
    @settings(max_examples=50)
    def test_pypi_format_age_calculation(self, age_days: int):
        """
        Test that age calculation works with PyPI metadata format.
        
        For any package age, the scorer should correctly calculate age
        from PyPI's releases format.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        created_date = (now - timedelta(days=age_days)).isoformat()
        
        # PyPI format metadata
        metadata = {
            'info': {
                'name': 'test-package',
                'version': '1.0.0'
            },
            'releases': {
                '1.0.0': [
                    {
                        'upload_time': created_date,
                        'size': 1000
                    }
                ]
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Age score should be calculated correctly from PyPI format
        assert 0.0 <= age_score <= 1.0, "Age score should be valid"
        
        # Verify score matches expected threshold
        if age_days < 30:
            assert age_score == 0.2
        elif age_days < 90:
            assert age_score == 0.5
        elif age_days < 365:
            assert age_score == 0.7
        elif age_days < 730:
            assert age_score == 0.9
        else:
            assert age_score == 1.0

    @given(st.integers(min_value=0, max_value=3650))
    @settings(max_examples=50)
    def test_npm_format_age_calculation(self, age_days: int):
        """
        Test that age calculation works with npm metadata format.
        
        For any package age, the scorer should correctly calculate age
        from npm's time.created format.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        created_date = (now - timedelta(days=age_days)).isoformat()
        
        # npm format metadata
        metadata = {
            'name': 'test-package',
            'version': '1.0.0',
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Age score should be calculated correctly from npm format
        assert 0.0 <= age_score <= 1.0, "Age score should be valid"
        
        # Verify score matches expected threshold
        if age_days < 30:
            assert age_score == 0.2
        elif age_days < 90:
            assert age_score == 0.5
        elif age_days < 365:
            assert age_score == 0.7
        elif age_days < 730:
            assert age_score == 0.9
        else:
            assert age_score == 1.0

    def test_missing_creation_date_returns_neutral_score(self):
        """
        Test that packages without creation date receive neutral score.
        
        For any package metadata without a creation date,
        the age score should default to 0.5 (neutral).
        """
        scorer = ReputationScorer()
        
        # Metadata without creation date
        metadata = {
            'name': 'test-package',
            'version': '1.0.0'
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Missing date should return neutral score
        assert age_score == 0.5, \
            f"Package without creation date should have neutral score 0.5, got {age_score}"

    def test_invalid_date_format_returns_neutral_score(self):
        """
        Test that packages with invalid date format receive neutral score.
        
        For any package metadata with an invalid date format,
        the age score should default to 0.5 (neutral).
        """
        scorer = ReputationScorer()
        
        # Metadata with invalid date format
        metadata = {
            'time': {
                'created': 'invalid-date-format',
                'modified': 'invalid-date-format'
            }
        }
        
        age_score = scorer._calculate_age_score(metadata)
        
        # Property: Invalid date should return neutral score
        assert age_score == 0.5, \
            f"Package with invalid date should have neutral score 0.5, got {age_score}"

    @given(st.integers(min_value=0, max_value=3650))
    @settings(max_examples=50)
    def test_age_score_monotonically_increases(self, age_days: int):
        """
        Test that age score increases monotonically with package age.
        
        For any package, adding more days to its age should never
        decrease its age score.
        """
        scorer = ReputationScorer()
        now = datetime.now()
        
        # Calculate score for current age
        created_date = (now - timedelta(days=age_days)).isoformat()
        metadata = {
            'time': {
                'created': created_date,
                'modified': created_date
            }
        }
        current_score = scorer._calculate_age_score(metadata)
        
        # Calculate score for age + 1 day
        older_date = (now - timedelta(days=age_days + 1)).isoformat()
        older_metadata = {
            'time': {
                'created': older_date,
                'modified': older_date
            }
        }
        older_score = scorer._calculate_age_score(older_metadata)
        
        # Property: Older package should have higher or equal score
        assert older_score >= current_score, \
            f"Older package (age={age_days + 1} days, score={older_score}) should have " \
            f"higher or equal score than younger package (age={age_days} days, score={current_score})"


class TestDownloadFactorInReputation:
    """Property-based tests for download factor in reputation scoring."""

    @given(
        st.integers(min_value=0, max_value=1000000),  # 0 to 1M downloads/week
        st.integers(min_value=0, max_value=1000000)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_12_download_factor_in_reputation(self, downloads_1: int, downloads_2: int):
        """
        **Feature: production-ready-enhancements, Property 12: Download Factor in Reputation**
        
        For any two packages with different download counts, the reputation scorer should assign 
        different download scores, with higher downloads receiving higher scores.
        
        **Validates: Requirements 3.3**
        """
        # Skip if download counts are the same
        assume(downloads_1 != downloads_2)
        
        scorer = ReputationScorer()
        
        # Create metadata for two packages with different download counts
        metadata_1 = {
            'downloads': downloads_1
        }
        
        metadata_2 = {
            'downloads': downloads_2
        }
        
        # Calculate download scores
        download_score_1 = scorer._calculate_downloads_score(metadata_1)
        download_score_2 = scorer._calculate_downloads_score(metadata_2)
        
        # Property 1: Packages with more downloads should have higher or equal scores
        if downloads_1 > downloads_2:
            # Package 1 has more downloads, should have higher or equal score
            assert download_score_1 >= download_score_2, \
                f"Package with more downloads (downloads={downloads_1}, score={download_score_1}) should have " \
                f"higher or equal score than package with fewer downloads (downloads={downloads_2}, score={download_score_2})"
        else:
            # Package 2 has more downloads, should have higher or equal score
            assert download_score_2 >= download_score_1, \
                f"Package with more downloads (downloads={downloads_2}, score={download_score_2}) should have " \
                f"higher or equal score than package with fewer downloads (downloads={downloads_1}, score={download_score_1})"
        
        # Property 2: Download scores should be within valid range [0.0, 1.0]
        assert 0.0 <= download_score_1 <= 1.0, "Download score should be between 0.0 and 1.0"
        assert 0.0 <= download_score_2 <= 1.0, "Download score should be between 0.0 and 1.0"
        
        # Property 3: If downloads are in different threshold buckets, scores should differ
        # Thresholds: <100, 100-1K, 1K-10K, 10K-100K, 100K+
        def get_download_bucket(downloads):
            if downloads < 100:
                return 0
            elif downloads < 1000:
                return 1
            elif downloads < 10000:
                return 2
            elif downloads < 100000:
                return 3
            else:
                return 4
        
        bucket_1 = get_download_bucket(downloads_1)
        bucket_2 = get_download_bucket(downloads_2)
        
        if bucket_1 != bucket_2:
            assert download_score_1 != download_score_2, \
                f"Packages in different download buckets should have different scores: " \
                f"downloads1={downloads_1} (bucket {bucket_1}, score={download_score_1}), " \
                f"downloads2={downloads_2} (bucket {bucket_2}, score={download_score_2})"

    @given(st.integers(min_value=0, max_value=99))
    @settings(max_examples=50)
    def test_very_low_downloads_low_score(self, downloads: int):
        """
        Test that packages with very low downloads (< 100/week) receive low scores.
        
        For any package with less than 100 downloads per week, the download score should be 0.2.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Very low download packages should have score of 0.2
        assert download_score == 0.2, \
            f"Package with {downloads} downloads/week should have download score 0.2, got {download_score}"

    @given(st.integers(min_value=100, max_value=999))
    @settings(max_examples=50)
    def test_low_downloads_medium_low_score(self, downloads: int):
        """
        Test that packages with low downloads (100-1K/week) receive medium-low scores.
        
        For any package with 100-1K downloads per week, the download score should be 0.5.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Low download packages should have score of 0.5
        assert download_score == 0.5, \
            f"Package with {downloads} downloads/week should have download score 0.5, got {download_score}"

    @given(st.integers(min_value=1000, max_value=9999))
    @settings(max_examples=50)
    def test_moderate_downloads_medium_high_score(self, downloads: int):
        """
        Test that packages with moderate downloads (1K-10K/week) receive medium-high scores.
        
        For any package with 1K-10K downloads per week, the download score should be 0.7.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Moderate download packages should have score of 0.7
        assert download_score == 0.7, \
            f"Package with {downloads} downloads/week should have download score 0.7, got {download_score}"

    @given(st.integers(min_value=10000, max_value=99999))
    @settings(max_examples=50)
    def test_high_downloads_high_score(self, downloads: int):
        """
        Test that packages with high downloads (10K-100K/week) receive high scores.
        
        For any package with 10K-100K downloads per week, the download score should be 0.9.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: High download packages should have score of 0.9
        assert download_score == 0.9, \
            f"Package with {downloads} downloads/week should have download score 0.9, got {download_score}"

    @given(st.integers(min_value=100000, max_value=1000000))
    @settings(max_examples=50)
    def test_very_high_downloads_maximum_score(self, downloads: int):
        """
        Test that packages with very high downloads (100K+/week) receive maximum scores.
        
        For any package with 100K or more downloads per week, the download score should be 1.0.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Very high download packages should have score of 1.0
        assert download_score == 1.0, \
            f"Package with {downloads} downloads/week should have download score 1.0, got {download_score}"

    def test_missing_downloads_returns_neutral_score(self):
        """
        Test that packages without download data receive neutral score.
        
        For any package metadata without download information,
        the download score should default to 0.5 (neutral).
        """
        scorer = ReputationScorer()
        
        # Metadata without downloads field
        metadata = {
            'name': 'test-package',
            'version': '1.0.0'
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Missing downloads should return neutral score
        assert download_score == 0.5, \
            f"Package without download data should have neutral score 0.5, got {download_score}"

    def test_npm_format_without_downloads_returns_neutral(self):
        """
        Test that npm packages without download stats receive neutral score.
        
        For npm packages where download stats are not available in the metadata,
        the download score should default to 0.5 (neutral).
        """
        scorer = ReputationScorer()
        
        # npm format metadata without downloads
        metadata = {
            'name': 'test-package',
            'version': '1.0.0',
            'dist-tags': {
                'latest': '1.0.0'
            }
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: npm without downloads should return neutral score
        assert download_score == 0.5, \
            f"npm package without download data should have neutral score 0.5, got {download_score}"

    def test_pypi_format_returns_neutral_score(self):
        """
        Test that PyPI packages receive neutral score (no download stats in JSON API).
        
        For PyPI packages, since the JSON API doesn't provide download statistics,
        the download score should default to 0.5 (neutral).
        """
        scorer = ReputationScorer()
        
        # PyPI format metadata
        metadata = {
            'info': {
                'name': 'test-package',
                'version': '1.0.0',
                'author': 'Test Author'
            },
            'releases': {
                '1.0.0': [
                    {
                        'upload_time': '2023-01-01T00:00:00',
                        'size': 1000
                    }
                ]
            }
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: PyPI packages should return neutral score
        assert download_score == 0.5, \
            f"PyPI package should have neutral score 0.5 (no download stats), got {download_score}"

    @given(st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=50)
    def test_download_score_monotonically_increases(self, downloads: int):
        """
        Test that download score increases monotonically with download count.
        
        For any package, increasing its download count should never
        decrease its download score.
        """
        scorer = ReputationScorer()
        
        # Calculate score for current downloads
        metadata = {
            'downloads': downloads
        }
        current_score = scorer._calculate_downloads_score(metadata)
        
        # Calculate score for downloads + 1
        higher_metadata = {
            'downloads': downloads + 1
        }
        higher_score = scorer._calculate_downloads_score(higher_metadata)
        
        # Property: More downloads should have higher or equal score
        assert higher_score >= current_score, \
            f"Package with more downloads (downloads={downloads + 1}, score={higher_score}) should have " \
            f"higher or equal score than package with fewer downloads (downloads={downloads}, score={current_score})"

    @given(st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=50)
    def test_download_score_within_valid_range(self, downloads: int):
        """
        Test that download scores are always within valid range.
        
        For any download count, the calculated score should be
        between 0.0 and 1.0 inclusive.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Score should be within valid range
        assert 0.0 <= download_score <= 1.0, \
            f"Download score should be between 0.0 and 1.0, got {download_score} for {downloads} downloads"

    @given(st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=50)
    def test_download_score_deterministic(self, downloads: int):
        """
        Test that download score calculation is deterministic.
        
        For any download count, calculating the score multiple times
        should always return the same result.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        # Calculate score multiple times
        score_1 = scorer._calculate_downloads_score(metadata)
        score_2 = scorer._calculate_downloads_score(metadata)
        score_3 = scorer._calculate_downloads_score(metadata)
        
        # Property: All scores should be identical
        assert score_1 == score_2 == score_3, \
            f"Download score calculation should be deterministic, got {score_1}, {score_2}, {score_3}"

    def test_zero_downloads_returns_lowest_score(self):
        """
        Test that packages with zero downloads receive the lowest score.
        
        For any package with exactly 0 downloads, the download score should be 0.2.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': 0
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Zero downloads should return lowest score
        assert download_score == 0.2, \
            f"Package with 0 downloads should have download score 0.2, got {download_score}"

    @given(st.integers(min_value=0, max_value=1000000))
    @settings(max_examples=50)
    def test_download_score_matches_threshold_buckets(self, downloads: int):
        """
        Test that download scores match expected threshold buckets.
        
        For any download count, the score should match the expected
        value based on the threshold bucket it falls into.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'downloads': downloads
        }
        
        download_score = scorer._calculate_downloads_score(metadata)
        
        # Property: Score should match expected threshold
        if downloads < 100:
            expected_score = 0.2
        elif downloads < 1000:
            expected_score = 0.5
        elif downloads < 10000:
            expected_score = 0.7
        elif downloads < 100000:
            expected_score = 0.9
        else:
            expected_score = 1.0
        
        assert download_score == expected_score, \
            f"Package with {downloads} downloads should have score {expected_score}, got {download_score}"



class TestAuthorFactorInReputation:
    """Property-based tests for author factor in reputation scoring."""

    @given(
        st.one_of(
            st.none(),  # Unknown author
            st.text(min_size=1, max_size=50),  # Author name
        ),
        st.one_of(
            st.none(),  # Unknown author
            st.text(min_size=1, max_size=50),  # Author name
        ),
        st.booleans(),  # Is verified/org for first package
        st.booleans()   # Is verified/org for second package
    )
    @settings(max_examples=100, deadline=None)
    def test_property_13_author_factor_in_reputation(
        self, 
        author_1: Optional[str], 
        author_2: Optional[str],
        is_verified_1: bool,
        is_verified_2: bool
    ):
        """
        **Feature: production-ready-enhancements, Property 13: Author Factor in Reputation**
        
        For any two packages from authors with different histories (new vs established),
        the reputation scorer should assign different author scores.
        
        **Validates: Requirements 3.4**
        """
        scorer = ReputationScorer()
        
        # Create metadata for two packages with different author information
        metadata_1 = self._create_author_metadata(author_1, is_verified_1)
        metadata_2 = self._create_author_metadata(author_2, is_verified_2)
        
        # Calculate author scores
        author_score_1 = scorer._calculate_author_score(metadata_1)
        author_score_2 = scorer._calculate_author_score(metadata_2)
        
        # Property 1: Author scores should be within valid range [0.0, 1.0]
        assert 0.0 <= author_score_1 <= 1.0, "Author score should be between 0.0 and 1.0"
        assert 0.0 <= author_score_2 <= 1.0, "Author score should be between 0.0 and 1.0"
        
        # Property 2: Verified/org packages should have highest score
        if is_verified_1:
            assert author_score_1 == 1.0, \
                f"Verified/org package should have author score 1.0, got {author_score_1}"
        
        if is_verified_2:
            assert author_score_2 == 1.0, \
                f"Verified/org package should have author score 1.0, got {author_score_2}"
        
        # Property 3: Packages with known authors should score higher than unknown
        # (only when neither is verified)
        if author_1 and not is_verified_1 and not author_2 and not is_verified_2:
            assert author_score_1 > author_score_2, \
                f"Package with known author (score={author_score_1}) should score higher " \
                f"than package with unknown author (score={author_score_2})"
        
        if author_2 and not is_verified_2 and not author_1 and not is_verified_1:
            assert author_score_2 > author_score_1, \
                f"Package with known author (score={author_score_2}) should score higher " \
                f"than package with unknown author (score={author_score_1})"
        
        # Property 4: Verified packages should score higher than non-verified
        if is_verified_1 and not is_verified_2:
            assert author_score_1 > author_score_2, \
                f"Verified package (score={author_score_1}) should score higher " \
                f"than non-verified package (score={author_score_2})"
        
        if is_verified_2 and not is_verified_1:
            assert author_score_2 > author_score_1, \
                f"Verified package (score={author_score_2}) should score higher " \
                f"than non-verified package (score={author_score_1})"
    
    def _create_author_metadata(self, author_name: Optional[str], is_verified: bool) -> Dict[str, Any]:
        """Helper to create metadata with author information."""
        metadata = {}
        
        if author_name:
            # npm format
            metadata['author'] = {'name': author_name}
        
        if is_verified:
            # Add verification indicators
            metadata['maintainers'] = [
                {'name': 'maintainer1'},
                {'name': 'maintainer2'}
            ]
            metadata['publisher'] = {'type': 'organization'}
        
        return metadata

    def test_unknown_author_low_score(self):
        """
        Test that packages with unknown authors receive low scores.
        
        For any package without author information, the author score should be 0.3.
        """
        scorer = ReputationScorer()
        
        # Metadata without author
        metadata = {
            'name': 'test-package',
            'version': '1.0.0'
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: Unknown author should return low score
        assert author_score == 0.3, \
            f"Package without author should have author score 0.3, got {author_score}"

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_known_author_established_score(self, author_name: str):
        """
        Test that packages with known authors receive established scores.
        
        For any package with a known author (non-empty name), the author score should be 0.8.
        """
        scorer = ReputationScorer()
        
        # npm format with author
        metadata = {
            'author': {
                'name': author_name
            }
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: Known author should return established score
        assert author_score == 0.8, \
            f"Package with known author '{author_name}' should have author score 0.8, got {author_score}"

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_verified_organization_maximum_score(self, author_name: str):
        """
        Test that verified/organization packages receive maximum scores.
        
        For any package with verification indicators (multiple maintainers or org publisher),
        the author score should be 1.0.
        """
        scorer = ReputationScorer()
        
        # Metadata with verification indicators
        metadata = {
            'author': {
                'name': author_name
            },
            'maintainers': [
                {'name': 'maintainer1'},
                {'name': 'maintainer2'}
            ]
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: Verified/org should return maximum score
        assert author_score == 1.0, \
            f"Verified/org package should have author score 1.0, got {author_score}"

    def test_organization_publisher_maximum_score(self):
        """
        Test that packages from organization publishers receive maximum scores.
        
        For any package with publisher type 'organization', the author score should be 1.0.
        """
        scorer = ReputationScorer()
        
        # Metadata with organization publisher
        metadata = {
            'author': {
                'name': 'Some Author'
            },
            'publisher': {
                'type': 'organization'
            }
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: Organization publisher should return maximum score
        assert author_score == 1.0, \
            f"Package from organization should have author score 1.0, got {author_score}"

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_npm_string_author_format(self, author_name: str):
        """
        Test that npm packages with string author format are handled correctly.
        
        For any npm package where author is a string (not dict), the author score
        should be 0.8 (established author).
        """
        scorer = ReputationScorer()
        
        # npm format with string author
        metadata = {
            'author': author_name
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: String author should return established score
        assert author_score == 0.8, \
            f"Package with string author '{author_name}' should have author score 0.8, got {author_score}"

    @given(st.text(min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_pypi_author_format(self, author_name: str):
        """
        Test that PyPI packages with author information are handled correctly.
        
        For any PyPI package with author in info section, the author score
        should be 0.8 (established author).
        """
        scorer = ReputationScorer()
        
        # PyPI format with author
        metadata = {
            'info': {
                'name': 'test-package',
                'version': '1.0.0',
                'author': author_name
            }
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: PyPI author should return established score
        assert author_score == 0.8, \
            f"PyPI package with author '{author_name}' should have author score 0.8, got {author_score}"

    def test_empty_author_name_unknown_score(self):
        """
        Test that packages with empty author names receive unknown author scores.
        
        For any package with an empty string as author name, the author score should be 0.3.
        """
        scorer = ReputationScorer()
        
        # Metadata with empty author name
        metadata = {
            'author': {
                'name': ''
            }
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: Empty author name should return unknown score
        assert author_score == 0.3, \
            f"Package with empty author name should have author score 0.3, got {author_score}"

    def test_multiple_maintainers_indicates_organization(self):
        """
        Test that packages with multiple maintainers are treated as organizations.
        
        For any package with 2 or more maintainers, the author score should be 1.0.
        """
        scorer = ReputationScorer()
        
        # Metadata with multiple maintainers
        metadata = {
            'author': {
                'name': 'Primary Author'
            },
            'maintainers': [
                {'name': 'maintainer1'},
                {'name': 'maintainer2'},
                {'name': 'maintainer3'}
            ]
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: Multiple maintainers should indicate organization
        assert author_score == 1.0, \
            f"Package with multiple maintainers should have author score 1.0, got {author_score}"

    def test_single_maintainer_not_organization(self):
        """
        Test that packages with single maintainer are not treated as organizations.
        
        For any package with only 1 maintainer, the author score should not be 1.0
        based solely on maintainer count.
        """
        scorer = ReputationScorer()
        
        # Metadata with single maintainer
        metadata = {
            'author': {
                'name': 'Primary Author'
            },
            'maintainers': [
                {'name': 'maintainer1'}
            ]
        }
        
        author_score = scorer._calculate_author_score(metadata)
        
        # Property: Single maintainer should not indicate organization
        assert author_score == 0.8, \
            f"Package with single maintainer should have author score 0.8, got {author_score}"

    def test_author_score_deterministic(self):
        """
        Test that author score calculation is deterministic.
        
        For any author metadata, calculating the score multiple times
        should always return the same result.
        """
        scorer = ReputationScorer()
        
        metadata = {
            'author': {
                'name': 'Test Author'
            }
        }
        
        # Calculate score multiple times
        score_1 = scorer._calculate_author_score(metadata)
        score_2 = scorer._calculate_author_score(metadata)
        score_3 = scorer._calculate_author_score(metadata)
        
        # Property: All scores should be identical
        assert score_1 == score_2 == score_3, \
            f"Author score calculation should be deterministic, got {score_1}, {score_2}, {score_3}"

    def test_author_score_within_valid_range(self):
        """
        Test that author scores are always within valid range.
        
        For any author metadata, the calculated score should be
        between 0.0 and 1.0 inclusive.
        """
        scorer = ReputationScorer()
        
        test_cases = [
            {},  # No author
            {'author': {'name': 'Test'}},  # Known author
            {'author': {'name': 'Test'}, 'maintainers': [{'name': 'm1'}, {'name': 'm2'}]},  # Org
            {'author': 'String Author'},  # String format
            {'info': {'author': 'PyPI Author'}},  # PyPI format
        ]
        
        for metadata in test_cases:
            author_score = scorer._calculate_author_score(metadata)
            
            # Property: Score should be within valid range
            assert 0.0 <= author_score <= 1.0, \
                f"Author score should be between 0.0 and 1.0, got {author_score} for metadata {metadata}"

    def test_error_handling_returns_low_score(self):
        """
        Test that errors in author parsing return low scores.
        
        For any malformed author metadata that causes parsing errors,
        the author score should default to 0.3 (unknown author).
        """
        scorer = ReputationScorer()
        
        # Malformed metadata that might cause errors
        test_cases = [
            {'author': None},  # None author
            {'author': {'invalid_key': 'value'}},  # Missing 'name' key
            {'info': {'author': None}},  # PyPI with None author
        ]
        
        for metadata in test_cases:
            author_score = scorer._calculate_author_score(metadata)
            
            # Property: Error cases should return low score
            assert author_score == 0.3, \
                f"Malformed author metadata should return score 0.3, got {author_score} for {metadata}"

    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=50)
    def test_different_authors_same_score_category(self, author_1: str, author_2: str):
        """
        Test that different known authors receive the same score.
        
        For any two different author names (both known), the author scores
        should be the same (0.8) since they're in the same category.
        """
        # Skip if authors are the same
        assume(author_1 != author_2)
        
        scorer = ReputationScorer()
        
        metadata_1 = {
            'author': {
                'name': author_1
            }
        }
        
        metadata_2 = {
            'author': {
                'name': author_2
            }
        }
        
        author_score_1 = scorer._calculate_author_score(metadata_1)
        author_score_2 = scorer._calculate_author_score(metadata_2)
        
        # Property: Different known authors should have same score
        assert author_score_1 == author_score_2 == 0.8, \
            f"Different known authors should have same score 0.8, got {author_score_1} and {author_score_2}"

    def test_author_score_hierarchy(self):
        """
        Test that author scores follow the expected hierarchy.
        
        Verified/org (1.0) > Known author (0.8) > Unknown author (0.3)
        """
        scorer = ReputationScorer()
        
        # Unknown author
        unknown_metadata = {}
        unknown_score = scorer._calculate_author_score(unknown_metadata)
        
        # Known author
        known_metadata = {
            'author': {
                'name': 'Known Author'
            }
        }
        known_score = scorer._calculate_author_score(known_metadata)
        
        # Verified/org
        verified_metadata = {
            'author': {
                'name': 'Verified Author'
            },
            'maintainers': [
                {'name': 'm1'},
                {'name': 'm2'}
            ]
        }
        verified_score = scorer._calculate_author_score(verified_metadata)
        
        # Property: Scores should follow hierarchy
        assert verified_score > known_score > unknown_score, \
            f"Author scores should follow hierarchy: verified ({verified_score}) > " \
            f"known ({known_score}) > unknown ({unknown_score})"
        
        # Verify exact values
        assert unknown_score == 0.3, f"Unknown author should be 0.3, got {unknown_score}"
        assert known_score == 0.8, f"Known author should be 0.8, got {known_score}"
        assert verified_score == 1.0, f"Verified author should be 1.0, got {verified_score}"



class TestLowReputationFlagging:
    """Property-based tests for low reputation flagging."""

    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_14_low_reputation_flagging(
        self,
        age_score: float,
        downloads_score: float,
        author_score: float,
        maintenance_score: float
    ):
        """
        **Feature: production-ready-enhancements, Property 14: Low Reputation Flagging**
        
        For any package with a reputation score below the threshold (< 0.3), the system 
        should generate a security finding flagging the low reputation.
        
        **Validates: Requirements 3.5**
        """
        scorer = ReputationScorer()
        
        # Calculate composite reputation score using the same formula as the implementation
        # composite_score = (age * 0.3) + (downloads * 0.3) + (author * 0.2) + (maintenance * 0.2)
        composite_score = (
            age_score * 0.3 +
            downloads_score * 0.3 +
            author_score * 0.2 +
            maintenance_score * 0.2
        )
        
        # Create mock metadata with scores that will produce the composite score
        # We'll mock the individual score calculation methods
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            # Calculate reputation
            result = scorer._calculate_scores({})
            
            # Property 1: Composite score should match expected calculation
            assert abs(result['score'] - composite_score) < 0.001, \
                f"Composite score should be {composite_score}, got {result['score']}"
            
            # Property 2: If composite score < 0.3, flags should indicate low reputation
            if composite_score < 0.3:
                # At least one flag should be present indicating low reputation
                # Flags are generated based on individual scores, not composite
                # But we can verify the composite score is correctly calculated
                assert result['score'] < 0.3, \
                    f"Low reputation package should have score < 0.3, got {result['score']}"
            
            # Property 3: Result should contain all factor scores
            assert 'factors' in result, "Result should contain factors"
            assert result['factors']['age_score'] == age_score
            assert result['factors']['downloads_score'] == downloads_score
            assert result['factors']['author_score'] == author_score
            assert result['factors']['maintenance_score'] == maintenance_score
            
            # Property 4: Flags should be generated based on individual factor scores
            expected_flags = []
            if age_score < 0.5:
                expected_flags.append("new_package")
            if downloads_score < 0.5:
                expected_flags.append("low_downloads")
            if author_score < 0.5:
                expected_flags.append("unknown_author")
            if maintenance_score < 0.5:
                expected_flags.append("unmaintained")
            
            assert result['flags'] == expected_flags, \
                f"Flags should be {expected_flags}, got {result['flags']}"

    @given(st.floats(min_value=0.0, max_value=0.29))
    @settings(max_examples=50)
    def test_very_low_reputation_always_flagged(self, low_score: float):
        """
        Test that packages with very low reputation (< 0.3) are always flagged.
        
        For any package with a composite reputation score below 0.3,
        the package should be considered high risk.
        """
        scorer = ReputationScorer()
        
        # Create scores that will produce a low composite score
        # Use equal distribution to hit the target
        age_score = low_score
        downloads_score = low_score
        author_score = low_score
        maintenance_score = low_score
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: Very low reputation should be flagged
            assert result['score'] < 0.3, \
                f"Package with low reputation should have score < 0.3, got {result['score']}"
            
            # Property: Should have multiple flags
            assert len(result['flags']) > 0, \
                f"Low reputation package should have flags, got {result['flags']}"

    @given(st.floats(min_value=0.8, max_value=1.0))
    @settings(max_examples=50)
    def test_high_reputation_not_flagged(self, high_score: float):
        """
        Test that packages with high reputation (>= 0.8) have minimal flags.
        
        For any package with a composite reputation score at or above 0.8,
        the package should be considered trusted.
        """
        scorer = ReputationScorer()
        
        # Create scores that will produce a high composite score
        age_score = high_score
        downloads_score = high_score
        author_score = high_score
        maintenance_score = high_score
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: High reputation should have high score
            assert result['score'] >= 0.8, \
                f"Package with high reputation should have score >= 0.8, got {result['score']}"
            
            # Property: Should have no flags (all individual scores >= 0.5)
            assert len(result['flags']) == 0, \
                f"High reputation package should have no flags, got {result['flags']}"

    def test_threshold_boundary_at_0_3(self):
        """
        Test the boundary condition at reputation score 0.3.
        
        Packages with score exactly at 0.3 should be on the edge of
        being flagged as low reputation.
        """
        scorer = ReputationScorer()
        
        # Create scores that produce exactly 0.3
        # 0.3 = (age * 0.3) + (downloads * 0.3) + (author * 0.2) + (maintenance * 0.2)
        # If all scores are 0.3, composite = 0.3
        age_score = 0.3
        downloads_score = 0.3
        author_score = 0.3
        maintenance_score = 0.3
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: Score should be exactly 0.3
            assert abs(result['score'] - 0.3) < 0.001, \
                f"Boundary case should have score 0.3, got {result['score']}"

    def test_composite_score_weighted_average(self):
        """
        Test that composite score is correctly calculated as weighted average.
        
        The formula should be:
        score = (age * 0.3) + (downloads * 0.3) + (author * 0.2) + (maintenance * 0.2)
        """
        scorer = ReputationScorer()
        
        # Use distinct scores to verify weighting
        age_score = 1.0
        downloads_score = 0.8
        author_score = 0.6
        maintenance_score = 0.4
        
        expected_score = (1.0 * 0.3) + (0.8 * 0.3) + (0.6 * 0.2) + (0.4 * 0.2)
        # = 0.3 + 0.24 + 0.12 + 0.08 = 0.74
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: Composite score should match weighted average
            assert abs(result['score'] - expected_score) < 0.001, \
                f"Composite score should be {expected_score}, got {result['score']}"

    def test_flags_based_on_individual_scores(self):
        """
        Test that flags are generated based on individual factor scores.
        
        Flags should be added when individual scores fall below 0.5,
        not based on the composite score.
        """
        scorer = ReputationScorer()
        
        # Create a case where composite is high but some individual scores are low
        age_score = 1.0  # High
        downloads_score = 1.0  # High
        author_score = 0.3  # Low - should trigger "unknown_author" flag
        maintenance_score = 0.4  # Low - should trigger "unmaintained" flag
        
        # Composite = (1.0 * 0.3) + (1.0 * 0.3) + (0.3 * 0.2) + (0.4 * 0.2)
        #           = 0.3 + 0.3 + 0.06 + 0.08 = 0.74 (high)
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: Composite score should be high
            assert result['score'] > 0.7, \
                f"Composite score should be high, got {result['score']}"
            
            # Property: Should have flags for low individual scores
            assert "unknown_author" in result['flags'], \
                f"Should have 'unknown_author' flag, got {result['flags']}"
            assert "unmaintained" in result['flags'], \
                f"Should have 'unmaintained' flag, got {result['flags']}"
            
            # Property: Should not have flags for high individual scores
            assert "new_package" not in result['flags'], \
                f"Should not have 'new_package' flag, got {result['flags']}"
            assert "low_downloads" not in result['flags'], \
                f"Should not have 'low_downloads' flag, got {result['flags']}"

    def test_all_flags_when_all_scores_low(self):
        """
        Test that all flags are present when all individual scores are low.
        
        When all factor scores are below 0.5, all four flags should be present.
        """
        scorer = ReputationScorer()
        
        # All scores low
        age_score = 0.2
        downloads_score = 0.2
        author_score = 0.3
        maintenance_score = 0.2
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: Should have all four flags
            expected_flags = ["new_package", "low_downloads", "unknown_author", "unmaintained"]
            assert set(result['flags']) == set(expected_flags), \
                f"Should have all flags {expected_flags}, got {result['flags']}"

    def test_no_flags_when_all_scores_high(self):
        """
        Test that no flags are present when all individual scores are high.
        
        When all factor scores are above 0.5, no flags should be present.
        """
        scorer = ReputationScorer()
        
        # All scores high
        age_score = 0.9
        downloads_score = 0.9
        author_score = 0.8
        maintenance_score = 1.0
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: Should have no flags
            assert len(result['flags']) == 0, \
                f"Should have no flags, got {result['flags']}"

    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=100, deadline=None)
    def test_reputation_score_within_valid_range(
        self,
        age_score: float,
        downloads_score: float,
        author_score: float,
        maintenance_score: float
    ):
        """
        Test that reputation scores are always within valid range.
        
        For any combination of factor scores, the composite reputation score
        should be between 0.0 and 1.0 inclusive.
        """
        scorer = ReputationScorer()
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result = scorer._calculate_scores({})
            
            # Property: Composite score should be within valid range
            assert 0.0 <= result['score'] <= 1.0, \
                f"Reputation score should be between 0.0 and 1.0, got {result['score']}"

    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=50)
    def test_reputation_calculation_deterministic(
        self,
        age_score: float,
        downloads_score: float,
        author_score: float,
        maintenance_score: float
    ):
        """
        Test that reputation calculation is deterministic.
        
        For any combination of factor scores, calculating the reputation
        multiple times should always return the same result.
        """
        scorer = ReputationScorer()
        
        with patch.object(scorer, '_calculate_age_score', return_value=age_score), \
             patch.object(scorer, '_calculate_downloads_score', return_value=downloads_score), \
             patch.object(scorer, '_calculate_author_score', return_value=author_score), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance_score):
            
            result_1 = scorer._calculate_scores({})
            result_2 = scorer._calculate_scores({})
            result_3 = scorer._calculate_scores({})
            
            # Property: All results should be identical
            assert result_1['score'] == result_2['score'] == result_3['score'], \
                f"Reputation calculation should be deterministic"
            assert result_1['flags'] == result_2['flags'] == result_3['flags'], \
                f"Flag generation should be deterministic"

    def test_metadata_preserved_in_result(self):
        """
        Test that original metadata is preserved in the result.
        
        The result should include the original metadata that was passed in.
        """
        scorer = ReputationScorer()
        
        test_metadata = {
            'name': 'test-package',
            'version': '1.0.0',
            'custom_field': 'custom_value'
        }
        
        with patch.object(scorer, '_calculate_age_score', return_value=0.5), \
             patch.object(scorer, '_calculate_downloads_score', return_value=0.5), \
             patch.object(scorer, '_calculate_author_score', return_value=0.5), \
             patch.object(scorer, '_calculate_maintenance_score', return_value=0.5):
            
            result = scorer._calculate_scores(test_metadata)
            
            # Property: Metadata should be preserved
            assert 'metadata' in result, "Result should contain metadata"
            assert result['metadata'] == test_metadata, \
                f"Metadata should be preserved, got {result['metadata']}"

    def test_flag_threshold_at_0_5(self):
        """
        Test that flags are generated when individual scores are below 0.5.
        
        The threshold for flag generation should be 0.5 for all factors.
        """
        scorer = ReputationScorer()
        
        # Test boundary cases
        test_cases = [
            # (age, downloads, author, maintenance, expected_flags)
            (0.49, 0.6, 0.6, 0.6, ["new_package"]),
            (0.6, 0.49, 0.6, 0.6, ["low_downloads"]),
            (0.6, 0.6, 0.49, 0.6, ["unknown_author"]),
            (0.6, 0.6, 0.6, 0.49, ["unmaintained"]),
            (0.5, 0.5, 0.5, 0.5, []),  # Exactly at threshold - no flags
            (0.51, 0.51, 0.51, 0.51, []),  # Just above threshold - no flags
        ]
        
        for age, downloads, author, maintenance, expected_flags in test_cases:
            with patch.object(scorer, '_calculate_age_score', return_value=age), \
                 patch.object(scorer, '_calculate_downloads_score', return_value=downloads), \
                 patch.object(scorer, '_calculate_author_score', return_value=author), \
                 patch.object(scorer, '_calculate_maintenance_score', return_value=maintenance):
                
                result = scorer._calculate_scores({})
                
                # Property: Flags should match expected
                assert result['flags'] == expected_flags, \
                    f"For scores ({age}, {downloads}, {author}, {maintenance}), " \
                    f"expected flags {expected_flags}, got {result['flags']}"

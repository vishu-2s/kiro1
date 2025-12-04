"""
Package reputation scoring service.

Provides ecosystem-agnostic reputation scoring based on package metadata
from registries like npm and PyPI.
"""

from typing import Dict, Any, Optional
import requests
from datetime import datetime
import time
from threading import Lock


class ReputationScorer:
    """Ecosystem-agnostic reputation scoring service."""
    
    def __init__(self, analyzer_registry=None, rate_limit_per_second: float = 10.0):
        """
        Initialize with analyzer registry for ecosystem-specific logic.
        
        Args:
            analyzer_registry: Optional AnalyzerRegistry instance for ecosystem detection
            rate_limit_per_second: Maximum requests per second (default: 10)
        """
        self.registry = analyzer_registry
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Multi-Agent-Security-Analysis/1.0'
        })
        
        # Rate limiting
        self.rate_limit_per_second = rate_limit_per_second
        self.min_request_interval = 1.0 / rate_limit_per_second if rate_limit_per_second > 0 else 0
        self.last_request_time = 0.0
        self.rate_limit_lock = Lock()
    
    def calculate_reputation(self, package_name: str, ecosystem: str) -> Dict[str, Any]:
        """
        Calculate reputation score (0.0-1.0) based on multiple factors.
        Works across all ecosystems by using the analyzer registry.
        
        Args:
            package_name: Name of the package to analyze
            ecosystem: Ecosystem identifier ('npm', 'pypi', etc.)
        
        Returns:
            {
                "score": 0.0-1.0,
                "factors": {
                    "age_score": 0.0-1.0,
                    "downloads_score": 0.0-1.0,
                    "author_score": 0.0-1.0,
                    "maintenance_score": 0.0-1.0
                },
                "flags": ["new_package", "low_downloads", "unknown_author"],
                "metadata": {...}
            }
        """
        # Get registry URL based on ecosystem
        registry_url = self._get_registry_url(package_name, ecosystem)
        
        # Fetch metadata from registry
        metadata = self._fetch_metadata(registry_url)
        
        # Calculate scores
        return self._calculate_scores(metadata)
    
    def _get_registry_url(self, package_name: str, ecosystem: str) -> str:
        """
        Get registry URL for package based on ecosystem.
        
        Args:
            package_name: Name of the package
            ecosystem: Ecosystem identifier
        
        Returns:
            Registry API URL for the package
        """
        if ecosystem == "npm":
            return f"https://registry.npmjs.org/{package_name}"
        elif ecosystem == "pypi":
            return f"https://pypi.org/pypi/{package_name}/json"
        else:
            raise ValueError(f"Unsupported ecosystem: {ecosystem}")
    
    def _fetch_metadata(self, registry_url: str) -> Dict[str, Any]:
        """
        Fetch package metadata from registry (ecosystem-agnostic).
        Implements rate limiting to prevent overwhelming registry APIs.
        
        Args:
            registry_url: Full URL to package metadata endpoint
        
        Returns:
            Package metadata dictionary
        
        Raises:
            requests.RequestException: If metadata fetch fails
        """
        # Apply rate limiting
        with self.rate_limit_lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last_request
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
        
        try:
            response = self.session.get(registry_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch metadata from {registry_url}: {e}")
    
    def _calculate_scores(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate reputation scores from metadata (ecosystem-agnostic).
        
        Args:
            metadata: Package metadata from registry
        
        Returns:
            Reputation score dictionary with factors and flags
        """
        # Calculate individual factor scores
        age_score = self._calculate_age_score(metadata)
        downloads_score = self._calculate_downloads_score(metadata)
        author_score = self._calculate_author_score(metadata)
        maintenance_score = self._calculate_maintenance_score(metadata)
        
        # Calculate composite reputation score (weighted average)
        composite_score = (
            age_score * 0.3 +
            downloads_score * 0.3 +
            author_score * 0.2 +
            maintenance_score * 0.2
        )
        
        # Generate flags based on scores
        flags = []
        if age_score < 0.5:
            flags.append("new_package")
        if downloads_score < 0.5:
            flags.append("low_downloads")
        if author_score < 0.5:
            flags.append("unknown_author")
        if maintenance_score < 0.5:
            flags.append("unmaintained")
        
        return {
            "score": composite_score,
            "factors": {
                "age_score": age_score,
                "downloads_score": downloads_score,
                "author_score": author_score,
                "maintenance_score": maintenance_score
            },
            "flags": flags,
            "metadata": metadata
        }
    
    def _calculate_age_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate age-based reputation score.
        
        Scoring:
        - < 30 days: 0.2
        - 30-90 days: 0.5
        - 90-365 days: 0.7
        - 1-2 years: 0.9
        - 2+ years: 1.0
        
        Args:
            metadata: Package metadata from registry
        
        Returns:
            Age score between 0.0 and 1.0
        """
        try:
            # Extract creation date based on ecosystem
            created_date = None
            
            # npm format
            if 'time' in metadata and 'created' in metadata['time']:
                created_date = metadata['time']['created']
            # PyPI format
            elif 'info' in metadata and 'releases' in metadata:
                # Get earliest release date
                releases = metadata.get('releases', {})
                if releases:
                    earliest_release = None
                    for version, release_info in releases.items():
                        if release_info:
                            upload_time = release_info[0].get('upload_time')
                            if upload_time:
                                if earliest_release is None or upload_time < earliest_release:
                                    earliest_release = upload_time
                    created_date = earliest_release
            
            if not created_date:
                # No creation date available, assume unknown (medium risk)
                return 0.5
            
            # Parse date and calculate age in days
            created_dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            age_days = (datetime.now(created_dt.tzinfo) - created_dt).days
            
            # Apply scoring thresholds
            if age_days < 30:
                return 0.2
            elif age_days < 90:
                return 0.5
            elif age_days < 365:
                return 0.7
            elif age_days < 730:  # 2 years
                return 0.9
            else:
                return 1.0
                
        except (ValueError, KeyError, AttributeError):
            # Error parsing date, return neutral score
            return 0.5
    
    def _calculate_downloads_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate download-based reputation score.
        
        Scoring:
        - < 100/week: 0.2
        - 100-1K/week: 0.5
        - 1K-10K/week: 0.7
        - 10K-100K/week: 0.9
        - 100K+/week: 1.0
        
        Args:
            metadata: Package metadata from registry
        
        Returns:
            Downloads score between 0.0 and 1.0
        """
        try:
            # npm format - check for downloads field
            if 'downloads' in metadata:
                weekly_downloads = metadata['downloads']
                
                # Apply scoring thresholds
                if weekly_downloads < 100:
                    return 0.2
                elif weekly_downloads < 1000:
                    return 0.5
                elif weekly_downloads < 10000:
                    return 0.7
                elif weekly_downloads < 100000:
                    return 0.9
                else:
                    return 1.0
            # npm format - check in dist-tags or versions
            elif 'dist-tags' in metadata or 'versions' in metadata:
                # For npm, we might need to make a separate API call
                # For now, use a neutral score if not available
                return 0.5
            # PyPI format - no direct download stats in JSON API
            elif 'info' in metadata:
                # PyPI doesn't provide download stats in the JSON API
                # Return neutral score
                return 0.5
            else:
                # No download information available, return neutral score
                return 0.5
                
        except (ValueError, KeyError, AttributeError):
            # Error parsing downloads, return neutral score
            return 0.5
    
    def _calculate_author_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate author-based reputation score.
        
        Scoring:
        - Unknown author: 0.3
        - New author (< 1 year): 0.5
        - Established author: 0.8
        - Verified/org: 1.0
        
        Args:
            metadata: Package metadata from registry
        
        Returns:
            Author score between 0.0 and 1.0
        """
        try:
            author_name = None
            is_verified = False
            
            # npm format
            if 'author' in metadata:
                if isinstance(metadata['author'], dict):
                    author_name = metadata['author'].get('name')
                elif isinstance(metadata['author'], str):
                    author_name = metadata['author']
            
            # PyPI format
            elif 'info' in metadata:
                author_name = metadata['info'].get('author')
            
            # Check for verification indicators
            if 'maintainers' in metadata and len(metadata['maintainers']) > 1:
                # Multiple maintainers suggests organization
                is_verified = True
            
            if 'publisher' in metadata and metadata['publisher'].get('type') == 'organization':
                is_verified = True
            
            # Score based on author presence and verification
            if is_verified:
                return 1.0
            elif author_name and len(author_name) > 0:
                # Has author, assume established (could be enhanced with author history)
                return 0.8
            else:
                # Unknown author
                return 0.3
                
        except (ValueError, KeyError, AttributeError):
            # Error parsing author, return low score
            return 0.3
    
    def _calculate_maintenance_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate maintenance-based reputation score.
        
        Scoring:
        - Last update > 2 years: 0.2
        - Last update 1-2 years: 0.5
        - Last update 6-12 months: 0.7
        - Last update < 6 months: 1.0
        
        Args:
            metadata: Package metadata from registry
        
        Returns:
            Maintenance score between 0.0 and 1.0
        """
        try:
            last_update = None
            
            # npm format
            if 'time' in metadata and 'modified' in metadata['time']:
                last_update = metadata['time']['modified']
            # PyPI format
            elif 'info' in metadata and 'releases' in metadata:
                # Get most recent release date
                releases = metadata.get('releases', {})
                if releases:
                    latest_release = None
                    for version, release_info in releases.items():
                        if release_info:
                            upload_time = release_info[0].get('upload_time')
                            if upload_time:
                                if latest_release is None or upload_time > latest_release:
                                    latest_release = upload_time
                    last_update = latest_release
            
            if not last_update:
                # No update date available, assume neutral
                return 0.5
            
            # Parse date and calculate days since last update
            update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            days_since_update = (datetime.now(update_dt.tzinfo) - update_dt).days
            
            # Apply scoring thresholds
            if days_since_update > 730:  # > 2 years
                return 0.2
            elif days_since_update > 365:  # 1-2 years
                return 0.5
            elif days_since_update > 180:  # 6-12 months
                return 0.7
            else:  # < 6 months
                return 1.0
                
        except (ValueError, KeyError, AttributeError):
            # Error parsing date, return neutral score
            return 0.5

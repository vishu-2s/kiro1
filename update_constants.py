"""
Malicious package database update system for Multi-Agent Security Analysis System.
Integrates with OSV API to fetch latest malicious packages and maintains local cache.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import config
from constants import CACHE_FILE, CACHE_DURATION_HOURS
from tools.api_integration import OSVAPIClient


# OSVAPIClient is now imported from tools.api_integration


class MaliciousPackageCache:
    """Manages local cache of malicious package data."""
    
    def __init__(self, cache_file: str = None, cache_duration_hours: int = None):
        self.cache_file = cache_file or CACHE_FILE
        self.cache_duration_hours = cache_duration_hours or CACHE_DURATION_HOURS
        self.cache_path = Path(self.cache_file)
    
    def is_cache_valid(self) -> bool:
        """
        Check if the cache file exists and is within the valid time window.
        
        Returns:
            True if cache is valid, False otherwise
        """
        if not self.cache_path.exists():
            return False
        
        try:
            # Get file modification time
            cache_mtime = datetime.fromtimestamp(self.cache_path.stat().st_mtime)
            cache_age = datetime.now() - cache_mtime
            
            return cache_age < timedelta(hours=self.cache_duration_hours)
            
        except (OSError, ValueError) as e:
            print(f"Error checking cache validity: {e}")
            return False
    
    def load_cache(self) -> Optional[Dict[str, Any]]:
        """
        Load cached malicious package data.
        
        Returns:
            Cached data dictionary or None if cache is invalid/missing
        """
        if not self.is_cache_valid():
            return None
        
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate cache structure
            if not isinstance(data, dict) or 'malicious_packages' not in data:
                print("Invalid cache structure, ignoring cache")
                return None
                
            return data
            
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading cache: {e}")
            return None
    
    def save_cache(self, data: Dict[str, Any]) -> bool:
        """
        Save malicious package data to cache.
        
        Args:
            data: Dictionary containing malicious package data
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Add metadata to cache
            cache_data = {
                'malicious_packages': data,
                'last_updated': datetime.now().isoformat(),
                'cache_version': '1.0.0'
            }
            
            # Ensure directory exists
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = self.cache_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            temp_path.rename(self.cache_path)
            return True
            
        except (OSError, TypeError, ValueError) as e:
            print(f"Error saving cache: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Remove the cache file.
        
        Returns:
            True if removal was successful or file didn't exist, False otherwise
        """
        try:
            if self.cache_path.exists():
                self.cache_path.unlink()
            return True
        except OSError as e:
            print(f"Error clearing cache: {e}")
            return False


class MaliciousPackageUpdater:
    """Main class for updating malicious package database."""
    
    def __init__(self):
        self.osv_client = OSVAPIClient()
        self.cache = MaliciousPackageCache()
        self.ecosystems = ['npm', 'PyPI', 'Maven', 'RubyGems', 'crates.io', 'Go']
    
    def should_update_database(self, force_update: bool = False) -> bool:
        """
        Determine if the malicious package database should be updated.
        
        Args:
            force_update: If True, bypass cache validation
            
        Returns:
            True if update is needed, False otherwise
        """
        if force_update:
            return True
        
        if config.SKIP_MALICIOUS_DB_UPDATE:
            return False
        
        return not self.cache.is_cache_valid()
    
    def fetch_malicious_packages_from_osv(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch malicious packages from OSV API.
        
        Returns:
            Dictionary mapping ecosystems to lists of malicious package records
        """
        malicious_packages = {}
        
        # Known malicious packages to query (this is a starting point)
        # In practice, this would be expanded with more comprehensive lists
        known_malicious = {
            'npm': [
                'event-stream', 'eslint-scope', 'flatmap-stream', 'getcookies',
                'http-fetch', 'nodemv', 'crossenv', 'babelcli', 'cross-env.js'
            ],
            'PyPI': [
                'python3-dateutil', 'jeIlyfish', 'urllib4', 'requessts',
                'beautifulsoup', 'ctx', 'phpass'
            ],
            'Maven': [
                'org.apache.logging.log4j:log4j-core',
                'com.thoughtworks.xstream:xstream'
            ],
            'RubyGems': [
                'rest-client', 'strong_password', 'bootstrap-sass'
            ],
            'crates.io': [
                'rustdecimal', 'rand-core'
            ],
            'Go': [
                'github.com/beego/beego', 'github.com/unknwon/cae'
            ]
        }
        
        for ecosystem, packages in known_malicious.items():
            print(f"Fetching malicious packages for {ecosystem}...")
            ecosystem_packages = []
            
            for package in packages:
                response = self.osv_client.query_vulnerabilities(package, ecosystem)
                vulnerabilities = response.get_data().get('vulns', []) if response.is_success() else []
                
                if vulnerabilities:
                    for vuln in vulnerabilities:
                        package_info = {
                            'name': package,
                            'vulnerability_id': vuln.get('id', 'unknown'),
                            'summary': vuln.get('summary', 'No summary available'),
                            'severity': self._extract_severity(vuln),
                            'affected_versions': self._extract_affected_versions(vuln),
                            'reason': vuln.get('summary', 'Security vulnerability'),
                            'osv_data': vuln
                        }
                        ecosystem_packages.append(package_info)
                else:
                    # If no OSV data, use basic info
                    package_info = {
                        'name': package,
                        'vulnerability_id': 'manual',
                        'summary': 'Known malicious package',
                        'severity': 'high',
                        'affected_versions': ['*'],
                        'reason': 'Known malicious package',
                        'osv_data': None
                    }
                    ecosystem_packages.append(package_info)
                
                # Add small delay to be respectful to the API
                time.sleep(0.1)
            
            malicious_packages[ecosystem.lower()] = ecosystem_packages
        
        return malicious_packages
    
    def _extract_severity(self, vulnerability: Dict[str, Any]) -> str:
        """Extract severity from OSV vulnerability data."""
        severity = vulnerability.get('database_specific', {}).get('severity')
        if severity:
            return severity.lower()
        
        # Try to extract from CVSS score
        cvss = vulnerability.get('severity', [])
        if cvss:
            score = cvss[0].get('score')
            if score:
                if score >= 9.0:
                    return 'critical'
                elif score >= 7.0:
                    return 'high'
                elif score >= 4.0:
                    return 'medium'
                else:
                    return 'low'
        
        return 'medium'  # Default
    
    def _extract_affected_versions(self, vulnerability: Dict[str, Any]) -> List[str]:
        """Extract affected versions from OSV vulnerability data."""
        affected_versions = []
        
        affected = vulnerability.get('affected', [])
        for item in affected:
            ranges = item.get('ranges', [])
            for range_item in ranges:
                events = range_item.get('events', [])
                for event in events:
                    if 'introduced' in event:
                        affected_versions.append(f">={event['introduced']}")
                    if 'fixed' in event:
                        affected_versions.append(f"<{event['fixed']}")
        
        return affected_versions if affected_versions else ['*']
    
    def update_constants_file(self, malicious_packages: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Update the constants.py file with new malicious package data.
        
        Args:
            malicious_packages: Dictionary of malicious packages by ecosystem
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            constants_path = Path('constants.py')
            
            # Read current constants file
            with open(constants_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Convert our data format to the constants.py format
            formatted_packages = {}
            for ecosystem, packages in malicious_packages.items():
                formatted_packages[ecosystem] = []
                for pkg in packages:
                    formatted_pkg = {
                        'name': pkg['name'],
                        'version': pkg.get('affected_versions', ['*'])[0] if pkg.get('affected_versions') else '*',
                        'reason': pkg['reason']
                    }
                    formatted_packages[ecosystem].append(formatted_pkg)
            
            # Update the KNOWN_MALICIOUS_PACKAGES section
            # This is a simplified approach - in practice, you'd want more sophisticated parsing
            new_packages_str = json.dumps(formatted_packages, indent=4)
            
            # Find and replace the KNOWN_MALICIOUS_PACKAGES definition
            import re
            pattern = r'KNOWN_MALICIOUS_PACKAGES: Dict\[str, List\[Dict\]\] = \{.*?\n\}'
            replacement = f'KNOWN_MALICIOUS_PACKAGES: Dict[str, List[Dict]] = {new_packages_str}'
            
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            # Update the LAST_UPDATED timestamp
            timestamp_pattern = r'LAST_UPDATED = datetime\.now\(\)\.isoformat\(\)'
            timestamp_replacement = f'LAST_UPDATED = "{datetime.now().isoformat()}"'
            new_content = re.sub(timestamp_pattern, timestamp_replacement, new_content)
            
            # Write back to file
            with open(constants_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
            
        except (OSError, re.error) as e:
            print(f"Error updating constants file: {e}")
            return False
    
    def update_database(self, force_update: bool = False) -> bool:
        """
        Main method to update the malicious package database.
        
        Args:
            force_update: If True, bypass cache and force update
            
        Returns:
            True if update was successful, False otherwise
        """
        if not self.should_update_database(force_update):
            print("Database update not needed (cache is valid)")
            return True
        
        print("Updating malicious package database...")
        
        # Try to load from cache first
        if not force_update:
            cached_data = self.cache.load_cache()
            if cached_data:
                print("Using cached malicious package data")
                return self.update_constants_file(cached_data['malicious_packages'])
        
        # Fetch fresh data from OSV API
        try:
            malicious_packages = self.fetch_malicious_packages_from_osv()
            
            if not malicious_packages:
                print("No malicious packages fetched from OSV API")
                return False
            
            # Save to cache
            if not self.cache.save_cache(malicious_packages):
                print("Warning: Failed to save cache, but continuing with update")
            
            # Update constants file
            if self.update_constants_file(malicious_packages):
                print(f"Successfully updated malicious package database with {sum(len(pkgs) for pkgs in malicious_packages.values())} packages")
                return True
            else:
                print("Failed to update constants file")
                return False
                
        except Exception as e:
            print(f"Error during database update: {e}")
            return False


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update malicious package database')
    parser.add_argument('--force', action='store_true', help='Force update bypassing cache')
    parser.add_argument('--clear-cache', action='store_true', help='Clear cache before update')
    
    args = parser.parse_args()
    
    updater = MaliciousPackageUpdater()
    
    if args.clear_cache:
        print("Clearing cache...")
        updater.cache.clear_cache()
    
    success = updater.update_database(force_update=args.force)
    
    if success:
        print("Database update completed successfully")
        exit(0)
    else:
        print("Database update failed")
        exit(1)


if __name__ == '__main__':
    main()
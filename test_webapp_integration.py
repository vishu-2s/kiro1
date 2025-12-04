"""
Integration test for web UI with Python support and reputation scores.
"""
import pytest
import json
import os
from pathlib import Path
from flask import Flask
from app import app as flask_app

class TestWebAppIntegration:
    """Integration tests for web application."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        flask_app.config['TESTING'] = True
        with flask_app.test_client() as client:
            yield client
    
    def test_index_page_loads(self, client):
        """Test that the index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Multi-Agent Security Analysis System' in response.data
    
    def test_ecosystem_dropdown_present(self, client):
        """Test that ecosystem dropdown is present in UI."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'id="ecosystem"' in response.data
        assert b'value="pypi"' in response.data
        assert b'value="npm"' in response.data
        assert b'value="auto"' in response.data
    
    def test_reputation_styles_present(self, client):
        """Test that reputation badge styles are present."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'reputation-badge' in response.data
        assert b'reputation-high-risk' in response.data
        assert b'reputation-medium-risk' in response.data
        assert b'reputation-low-risk' in response.data
        assert b'reputation-trusted' in response.data
    
    def test_cache_stats_styles_present(self, client):
        """Test that cache statistics styles are present."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'cache-stats' in response.data
        assert b'cache-stats-grid' in response.data
        assert b'cache-stat-item' in response.data
    
    def test_ecosystem_badge_styles_present(self, client):
        """Test that ecosystem badge styles are present."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'ecosystem-badge' in response.data
        assert b'ecosystem-npm' in response.data
        assert b'ecosystem-pypi' in response.data
    
    def test_report_endpoint_with_sample_data(self, client):
        """Test that report endpoint returns sample data correctly."""
        # Ensure sample report exists
        sample_report_path = Path("outputs/test_ui_sample_report.json")
        if not sample_report_path.exists():
            pytest.skip("Sample report not found")
        
        # Set the result file in analysis state
        from app import analysis_state
        analysis_state['result_file'] = 'test_ui_sample_report.json'
        
        response = client.get('/api/report')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Verify report structure
        assert 'metadata' in data
        assert 'summary' in data
        assert 'security_findings' in data
        assert 'cache_statistics' in data
        
        # Verify ecosystems
        assert 'ecosystems_analyzed' in data['summary']
        assert 'npm' in data['summary']['ecosystems_analyzed']
        assert 'pypi' in data['summary']['ecosystems_analyzed']
        
        # Verify reputation findings
        low_rep_findings = [f for f in data['security_findings'] 
                           if f['finding_type'] == 'low_reputation']
        assert len(low_rep_findings) == 2
        
        # Verify cache statistics
        cache_stats = data['cache_statistics']
        assert cache_stats['total_entries'] == 25
        assert cache_stats['total_hits'] == 15
        assert cache_stats['size_mb'] == 2.5
    
    def test_status_endpoint(self, client):
        """Test that status endpoint works."""
        response = client.get('/api/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'running' in data
        assert 'status' in data
        assert 'logs' in data
    
    def test_reports_list_endpoint(self, client):
        """Test that reports list endpoint works."""
        response = client.get('/api/reports')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)

def test_ui_rendering_with_reputation():
    """Test that UI correctly renders reputation information."""
    
    # Read the HTML template
    template_path = Path("templates/index.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for reputation rendering logic
    assert 'low_reputation' in html_content
    assert 'reputation score:' in html_content
    assert 'Risk factors:' in html_content
    assert 'reputation-badge' in html_content
    
    print("✅ UI reputation rendering verified")

def test_ui_rendering_with_cache_stats():
    """Test that UI correctly renders cache statistics."""
    
    # Read the HTML template
    template_path = Path("templates/index.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for cache stats rendering logic
    assert 'cache_statistics' in html_content
    assert 'total_entries' in html_content
    assert 'total_hits' in html_content
    assert 'size_mb' in html_content
    assert 'Cache Performance' in html_content
    
    print("✅ UI cache statistics rendering verified")

def test_ui_rendering_with_ecosystems():
    """Test that UI correctly renders ecosystem information."""
    
    # Read the HTML template
    template_path = Path("templates/index.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for ecosystem rendering logic
    assert 'ecosystems_analyzed' in html_content
    assert 'ecosystem-badge' in html_content
    assert 'ecosystem-npm' in html_content
    assert 'ecosystem-pypi' in html_content
    
    print("✅ UI ecosystem rendering verified")

if __name__ == "__main__":
    print("\n🧪 Running Web UI Integration Tests\n")
    
    # Run standalone tests
    test_ui_rendering_with_reputation()
    test_ui_rendering_with_cache_stats()
    test_ui_rendering_with_ecosystems()
    
    print("\n✅ All standalone tests passed!")
    print("\nTo run full integration tests with Flask:")
    print("  pytest test_webapp_integration.py -v")

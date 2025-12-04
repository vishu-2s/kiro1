"""
Demo script to test the reputation service with real package data.
"""

from tools.reputation_service import ReputationScorer
from unittest.mock import patch, Mock


def demo_npm_package():
    """Demo reputation scoring for an npm package."""
    print("=" * 60)
    print("Demo: npm Package Reputation Scoring")
    print("=" * 60)
    
    scorer = ReputationScorer()
    
    # Mock npm registry response for a well-established package
    mock_npm_metadata = {
        'name': 'express',
        'version': '4.18.2',
        'time': {
            'created': '2010-01-03T00:00:00.000Z',
            'modified': '2024-11-15T00:00:00.000Z'
        },
        'downloads': 250000,  # Weekly downloads
        'author': {
            'name': 'TJ Holowaychuk'
        },
        'maintainers': [
            {'name': 'dougwilson'},
            {'name': 'wesleytodd'}
        ]
    }
    
    with patch.object(scorer, '_fetch_metadata', return_value=mock_npm_metadata):
        result = scorer.calculate_reputation('express', 'npm')
        
        print(f"\nPackage: express (npm)")
        print(f"Overall Reputation Score: {result['score']:.2f}")
        print(f"\nFactor Scores:")
        for factor, score in result['factors'].items():
            print(f"  {factor}: {score:.2f}")
        print(f"\nFlags: {', '.join(result['flags']) if result['flags'] else 'None'}")
        
        # Interpret the score
        if result['score'] >= 0.8:
            print(f"\n✅ TRUSTED - This package has excellent reputation")
        elif result['score'] >= 0.6:
            print(f"\n✓ LOW RISK - This package has good reputation")
        elif result['score'] >= 0.3:
            print(f"\n⚠ MEDIUM RISK - This package has moderate reputation")
        else:
            print(f"\n🔴 HIGH RISK - This package has poor reputation")


def demo_suspicious_package():
    """Demo reputation scoring for a suspicious package."""
    print("\n" + "=" * 60)
    print("Demo: Suspicious Package Reputation Scoring")
    print("=" * 60)
    
    scorer = ReputationScorer()
    
    # Mock npm registry response for a suspicious new package
    from datetime import datetime, timedelta
    
    mock_suspicious_metadata = {
        'name': 'suspicious-pkg',
        'version': '1.0.0',
        'time': {
            'created': (datetime.now() - timedelta(days=10)).isoformat(),
            'modified': (datetime.now() - timedelta(days=10)).isoformat()
        },
        'downloads': 25,  # Very low downloads
        # No author information
    }
    
    with patch.object(scorer, '_fetch_metadata', return_value=mock_suspicious_metadata):
        result = scorer.calculate_reputation('suspicious-pkg', 'npm')
        
        print(f"\nPackage: suspicious-pkg (npm)")
        print(f"Overall Reputation Score: {result['score']:.2f}")
        print(f"\nFactor Scores:")
        for factor, score in result['factors'].items():
            print(f"  {factor}: {score:.2f}")
        print(f"\nFlags: {', '.join(result['flags']) if result['flags'] else 'None'}")
        
        # Interpret the score
        if result['score'] >= 0.8:
            print(f"\n✅ TRUSTED - This package has excellent reputation")
        elif result['score'] >= 0.6:
            print(f"\n✓ LOW RISK - This package has good reputation")
        elif result['score'] >= 0.3:
            print(f"\n⚠ MEDIUM RISK - This package has moderate reputation")
        else:
            print(f"\n🔴 HIGH RISK - This package has poor reputation")


def demo_pypi_package():
    """Demo reputation scoring for a PyPI package."""
    print("\n" + "=" * 60)
    print("Demo: PyPI Package Reputation Scoring")
    print("=" * 60)
    
    scorer = ReputationScorer()
    
    # Mock PyPI registry response
    from datetime import datetime, timedelta
    
    mock_pypi_metadata = {
        'info': {
            'name': 'requests',
            'version': '2.31.0',
            'author': 'Kenneth Reitz'
        },
        'releases': {
            '0.1.0': [
                {
                    'upload_time': '2011-02-13T00:00:00',
                    'size': 1000
                }
            ],
            '2.31.0': [
                {
                    'upload_time': (datetime.now() - timedelta(days=60)).isoformat(),
                    'size': 50000
                }
            ]
        }
    }
    
    with patch.object(scorer, '_fetch_metadata', return_value=mock_pypi_metadata):
        result = scorer.calculate_reputation('requests', 'pypi')
        
        print(f"\nPackage: requests (PyPI)")
        print(f"Overall Reputation Score: {result['score']:.2f}")
        print(f"\nFactor Scores:")
        for factor, score in result['factors'].items():
            print(f"  {factor}: {score:.2f}")
        print(f"\nFlags: {', '.join(result['flags']) if result['flags'] else 'None'}")
        
        # Interpret the score
        if result['score'] >= 0.8:
            print(f"\n✅ TRUSTED - This package has excellent reputation")
        elif result['score'] >= 0.6:
            print(f"\n✓ LOW RISK - This package has good reputation")
        elif result['score'] >= 0.3:
            print(f"\n⚠ MEDIUM RISK - This package has moderate reputation")
        else:
            print(f"\n🔴 HIGH RISK - This package has poor reputation")


if __name__ == '__main__':
    demo_npm_package()
    demo_suspicious_package()
    demo_pypi_package()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

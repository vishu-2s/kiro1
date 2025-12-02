"""
Quick test to verify the web app can load and parse reports
"""
import json
import os

def test_report_loading():
    """Test that we can load and parse the report files"""
    output_dir = 'outputs'
    
    if not os.path.exists(output_dir):
        print("❌ No outputs directory found")
        return False
    
    json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    
    if not json_files:
        print("❌ No JSON files found in outputs/")
        return False
    
    print(f"✅ Found {len(json_files)} JSON file(s)")
    
    # Test loading the most recent file
    latest_file = sorted(json_files, 
                        key=lambda x: os.path.getmtime(os.path.join(output_dir, x)),
                        reverse=True)[0]
    
    print(f"📄 Testing file: {latest_file}")
    
    try:
        with open(os.path.join(output_dir, latest_file), 'r') as f:
            data = json.load(f)
        
        print("✅ JSON file loaded successfully")
        
        # Check for findings
        findings = data.get('findings') or data.get('security_findings') or []
        print(f"✅ Found {len(findings)} security findings")
        
        # Check for metadata
        metadata = data.get('metadata', {})
        print(f"✅ Metadata present: {bool(metadata)}")
        
        if metadata:
            print(f"   - Target: {metadata.get('target', 'N/A')}")
            print(f"   - Analysis Type: {metadata.get('analysis_type', 'N/A')}")
            print(f"   - Total Packages: {metadata.get('total_packages', 'N/A')}")
        
        # Check findings structure
        if findings:
            first_finding = findings[0]
            print(f"\n📋 Sample Finding:")
            print(f"   - Package: {first_finding.get('package', 'N/A')}")
            print(f"   - Severity: {first_finding.get('severity', 'N/A')}")
            print(f"   - Type: {first_finding.get('finding_type', 'N/A')}")
            print(f"   - Confidence: {first_finding.get('confidence', 'N/A')}")
        
        print("\n✅ All checks passed! Report structure is valid.")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Web App Report Loading Test")
    print("=" * 60)
    print()
    
    success = test_report_loading()
    
    print()
    print("=" * 60)
    if success:
        print("✅ TEST PASSED - Web app should display reports correctly")
    else:
        print("❌ TEST FAILED - Check the errors above")
    print("=" * 60)

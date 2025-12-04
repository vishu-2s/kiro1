"""
Test script to verify UI reputation display functionality
Opens the web UI in a browser to manually verify reputation findings display
"""
import webbrowser
import time
import subprocess
import sys
import os

def test_ui_display():
    """Start the Flask app and open browser to test UI"""
    print("Starting Flask web application...")
    print("This will open your browser to test the reputation display UI")
    print("\nTest checklist:")
    print("1. Click on the 'Report' tab")
    print("2. Verify you see both vulnerability and reputation findings for flatmap-stream")
    print("3. Check that reputation findings have:")
    print("   - 🛡️ icon (shield)")
    print("   - Reputation score badge")
    print("   - Factor scores (age, downloads, author, maintenance)")
    print("   - Risk factors list")
    print("4. Verify vulnerability findings have 🔒 icon (lock)")
    print("5. Check that summary statistics include both types of findings")
    print("\nPress Ctrl+C to stop the server when done testing\n")
    
    # Start Flask app
    try:
        # Open browser after a short delay
        time.sleep(2)
        webbrowser.open('http://localhost:5000')
        
        # Run Flask app
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n\nTest completed. Server stopped.")
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    # Verify the report file exists
    report_path = 'outputs/demo_ui_comprehensive_report.json'
    if not os.path.exists(report_path):
        print(f"Error: Report file not found at {report_path}")
        print("Please run an analysis first to generate the report.")
        sys.exit(1)
    
    test_ui_display()

"""
Test to verify that logs persist after analysis completion
"""
import time
import requests
import json

def test_log_persistence():
    """Test that logs remain visible after analysis completes"""
    base_url = "http://localhost:5000"
    
    print("Testing log persistence...")
    print("=" * 60)
    
    # 1. Check initial status
    print("\n1. Checking initial status...")
    response = requests.get(f"{base_url}/api/status")
    initial_status = response.json()
    print(f"   Initial status: {initial_status['status']}")
    print(f"   Initial logs count: {len(initial_status['logs'])}")
    
    # 2. Start an analysis
    print("\n2. Starting analysis...")
    analysis_data = {
        "mode": "local",
        "target": "C:\\Users\\VBSARA\\Downloads\\Downloadsflatmap-stream-preinstall_script"
    }
    response = requests.post(
        f"{base_url}/api/analyze",
        json=analysis_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"   ❌ Failed to start analysis: {response.text}")
        return False
    
    print("   ✅ Analysis started")
    
    # 3. Wait for analysis to complete
    print("\n3. Waiting for analysis to complete...")
    max_wait = 120  # 2 minutes max
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{base_url}/api/status")
        status = response.json()
        
        if not status['running']:
            print(f"   ✅ Analysis completed with status: {status['status']}")
            print(f"   Logs count: {len(status['logs'])}")
            break
        
        time.sleep(2)
    else:
        print("   ❌ Analysis timed out")
        return False
    
    # 4. Check logs immediately after completion
    print("\n4. Checking logs immediately after completion...")
    response = requests.get(f"{base_url}/api/status")
    completed_status = response.json()
    
    print(f"   Running: {completed_status['running']}")
    print(f"   Status: {completed_status['status']}")
    print(f"   Logs count: {len(completed_status['logs'])}")
    
    if len(completed_status['logs']) == 0:
        print("   ❌ FAIL: Logs were cleared after completion!")
        return False
    
    print("   ✅ Logs are present after completion")
    
    # 5. Wait a bit and check again (simulate user viewing logs)
    print("\n5. Waiting 5 seconds and checking logs again...")
    time.sleep(5)
    
    response = requests.get(f"{base_url}/api/status")
    later_status = response.json()
    
    print(f"   Running: {later_status['running']}")
    print(f"   Status: {later_status['status']}")
    print(f"   Logs count: {len(later_status['logs'])}")
    
    if len(later_status['logs']) == 0:
        print("   ❌ FAIL: Logs were cleared after waiting!")
        return False
    
    if len(later_status['logs']) != len(completed_status['logs']):
        print("   ❌ FAIL: Log count changed!")
        return False
    
    print("   ✅ Logs persisted correctly")
    
    # 6. Display last few log entries
    print("\n6. Last 5 log entries:")
    for log in later_status['logs'][-5:]:
        print(f"   [{log['timestamp']}] [{log['level'].upper()}] {log['message'][:80]}")
    
    print("\n" + "=" * 60)
    print("✅ TEST PASSED: Logs persist after analysis completion")
    return True

if __name__ == "__main__":
    try:
        success = test_log_persistence()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

"""
Update demo_ui_comprehensive_report.json with LLM-generated recommendations.
"""

import json
import shutil
from datetime import datetime

# Backup current report
backup_path = f"outputs/demo_ui_comprehensive_report_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
shutil.copy("outputs/demo_ui_comprehensive_report.json", backup_path)
print(f"✅ Created backup: {backup_path}")

# Load current report
with open("outputs/demo_ui_comprehensive_report.json") as f:
    report = json.load(f)

# Load test report with LLM recommendations
with open("outputs/test_llm_recommendations.json") as f:
    test_report = json.load(f)

# Update recommendations with LLM-generated content
report["recommendations"] = test_report["recommendations"]

# Add note about LLM enhancement
if "metadata" in report:
    report["metadata"]["llm_recommendations_enabled"] = True
    report["metadata"]["recommendations_source"] = "llm_enhanced"

# Save updated report
with open("outputs/demo_ui_comprehensive_report.json", "w") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("✅ Updated demo_ui_comprehensive_report.json with LLM recommendations")
print("\nRecommendations preview:")
print("=" * 80)
print(report["recommendations"][:500] + "...")
print("=" * 80)

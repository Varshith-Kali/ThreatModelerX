#!/usr/bin/env python3
"""
Script to scan demo applications for vulnerabilities using ThreatModelerX
"""
import os
import sys
import json
from pathlib import Path

# Add the backend directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.app.scanner.bandit_runner import BanditRunner
    from backend.app.scanner.retire_runner import RetireRunner
    from backend.app.scanner.semgrep_runner import SemgrepRunner
    from backend.app.workers.report_generator import ReportGenerator
    print("[PASS] Successfully imported scanner modules")
except ImportError as e:
    print(f"[FAIL] Error importing scanner modules: {e}")
    sys.exit(1)

def scan_python_flask_app():
    """Scan the Python Flask demo app for vulnerabilities"""
    print("\n=== Scanning Python Flask Demo App ===")
    
    flask_app_path = os.path.join(os.path.dirname(__file__), 'demo-apps', 'python-flask')
    
    if not os.path.exists(flask_app_path):
        print(f"[FAIL] Python Flask demo app not found at {flask_app_path}")
        return None
    
    print(f"[INFO] Scanning files in {flask_app_path}")
    
    findings = []
    
    # Run Bandit
    print("[INFO] Running Bandit...")
    bandit = BanditRunner()
    bandit_findings = bandit.run(flask_app_path)
    print(f"[INFO] Bandit found {len(bandit_findings)} issues")
    findings.extend(bandit_findings)
    
    # Run Semgrep
    print("[INFO] Running Semgrep...")
    semgrep = SemgrepRunner()
    semgrep_findings = semgrep.run(flask_app_path)
    print(f"[INFO] Semgrep found {len(semgrep_findings)} issues")
    findings.extend(semgrep_findings)
    
    print(f"[INFO] Found {len(findings)} potential vulnerabilities")
    
    # Convert findings to dict for report
    findings_dict = [f.model_dump() for f in findings]
    
    return {
        "app_name": "Python Flask Demo App",
        "app_path": flask_app_path,
        "findings": findings_dict,
        "scan_type": "SAST (Python)"
    }

def scan_node_express_app():
    """Scan the Node Express demo app for vulnerabilities"""
    print("\n=== Scanning Node Express Demo App ===")
    
    express_app_path = os.path.join(os.path.dirname(__file__), 'demo-apps', 'node-express')
    
    if not os.path.exists(express_app_path):
        print(f"[FAIL] Node Express demo app not found at {express_app_path}")
        return None
    
    print(f"[INFO] Scanning files in {express_app_path}")
    
    findings = []
    
    # Run Semgrep
    print("[INFO] Running Semgrep...")
    semgrep = SemgrepRunner()
    semgrep_findings = semgrep.run(express_app_path)
    print(f"[INFO] Semgrep found {len(semgrep_findings)} issues")
    findings.extend(semgrep_findings)
    
    # Run Retire.js
    print("[INFO] Running Retire.js...")
    retire = RetireRunner()
    retire_findings = retire.run(express_app_path)
    print(f"[INFO] Retire.js found {len(retire_findings)} issues")
    findings.extend(retire_findings)
    
    print(f"[INFO] Found {len(findings)} potential vulnerabilities")
    
    # Convert findings to dict for report
    findings_dict = [f.model_dump() for f in findings]
    
    return {
        "app_name": "Node Express Demo App",
        "app_path": express_app_path,
        "findings": findings_dict,
        "scan_type": "SAST (JavaScript)"
    }

def generate_vulnerability_report(scan_results):
    """Generate a comprehensive vulnerability report"""
    print("\n=== Generating Vulnerability Report ===")
    
    if not scan_results:
        print("[FAIL] No scan results to report")
        return
    
    # Count total vulnerabilities
    total_vulnerabilities = sum(len(result["findings"]) for result in scan_results if result)
    
    print(f"[INFO] Total vulnerabilities found: {total_vulnerabilities}")
    
    # Generate a report using the ReportGenerator
    try:
        report_generator = ReportGenerator()
        
        # Prepare data for the report
        report_data = {
            "scan_id": "demo-apps-scan",
            "timestamp": "2023-06-01T12:00:00Z",
            "findings": [],
            "summary": {
                "total_vulnerabilities": total_vulnerabilities,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0
            }
        }
        
        # Combine all findings
        for result in scan_results:
            if not result:
                continue
                
            for finding in result["findings"]:
                # Add app info to each finding
                finding["app_name"] = result["app_name"]
                finding["scan_type"] = result["scan_type"]
                
                # Count by severity
                severity = str(finding.get("severity", "medium")).lower()
                if "high" in severity or "critical" in severity:
                    report_data["summary"]["high_severity"] += 1
                elif "medium" in severity:
                    report_data["summary"]["medium_severity"] += 1
                elif "low" in severity:
                    report_data["summary"]["low_severity"] += 1
                
                report_data["findings"].append(finding)
        
        # Save raw JSON data
        with open("demo_apps_vulnerabilities.json", "w") as f:
            json.dump(report_data, f, indent=2, default=str)
            
        print(f"[PASS] Raw vulnerability data saved to demo_apps_vulnerabilities.json")
        
        # Generate HTML report
        try:
            report_path = report_generator.generate_report(report_data, format="html")
            print(f"[PASS] HTML report generated at {report_path}")
            return report_path
        except Exception as e:
            print(f"[WARN] HTML report generation failed: {e}")
            return "demo_apps_vulnerabilities.json"
        
    except Exception as e:
        print(f"[FAIL] Error generating report: {e}")
        return None

def main():
    """Main function to scan demo apps and generate reports"""
    print("=== ThreatModelerX Demo Apps Vulnerability Scanner ===")
    
    scan_results = []
    
    # Scan Python Flask app
    flask_results = scan_python_flask_app()
    if flask_results:
        scan_results.append(flask_results)
    
    # Scan Node Express app
    express_results = scan_node_express_app()
    if express_results:
        scan_results.append(express_results)
    
    # Generate comprehensive report
    report_path = generate_vulnerability_report(scan_results)
    
    print("\n=== Scan Summary ===")
    print(f"[INFO] Apps scanned: {len(scan_results)}")
    print(f"[INFO] Report generated: {report_path if report_path else 'Failed'}")
    
    if not scan_results:
        print("[FAIL] No apps were successfully scanned")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
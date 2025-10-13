#!/usr/bin/env python3
"""
Script to scan demo applications for vulnerabilities using AutoThreatMap
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
    from backend.app.scanner.zap_runner import ZapRunner
    from backend.app.scanner.spotbugs_runner import SpotBugsRunner
    from backend.app.scanner.gosec_runner import GosecRunner
    from backend.app.workers.report_generator import ReportGenerator
    print("✅ Successfully imported scanner modules")
except ImportError as e:
    print(f"❌ Error importing scanner modules: {e}")
    sys.exit(1)

def scan_python_flask_app():
    """Scan the Python Flask demo app for vulnerabilities"""
    print("\n=== Scanning Python Flask Demo App ===")
    
    flask_app_path = os.path.join(os.path.dirname(__file__), 'demo-apps', 'python-flask')
    
    if not os.path.exists(flask_app_path):
        print(f"❌ Python Flask demo app not found at {flask_app_path}")
        return None
    
    print(f"📂 Scanning files in {flask_app_path}")
    
    # Use Bandit runner to scan the Python code
    bandit_runner = BanditRunner()
    findings = bandit_runner.run(flask_app_path)
    
    # Use Semgrep runner for additional checks
    try:
        semgrep_runner = SemgrepRunner()
        semgrep_findings = semgrep_runner.run(flask_app_path)
        findings.extend(semgrep_findings)
    except Exception as e:
        print(f"⚠️ Semgrep scan failed: {e}")
    
    print(f"🔍 Found {len(findings)} potential vulnerabilities")
    
    return {
        "app_name": "Python Flask Demo App",
        "app_path": flask_app_path,
        "findings": findings,
        "scan_type": "SAST (Python)"
    }

def scan_node_express_app():
    """Scan the Node Express demo app for vulnerabilities"""
    print("\n=== Scanning Node Express Demo App ===")
    
    express_app_path = os.path.join(os.path.dirname(__file__), 'demo-apps', 'node-express')
    
    if not os.path.exists(express_app_path):
        print(f"❌ Node Express demo app not found at {express_app_path}")
        return None
    
    print(f"📂 Scanning files in {express_app_path}")
    
    # Use RetireJS runner to scan for vulnerable dependencies
    findings = []
    try:
        retire_runner = RetireRunner()
        retire_findings = retire_runner.run(express_app_path)
        findings.extend(retire_findings)
    except Exception as e:
        print(f"⚠️ RetireJS scan failed: {e}")
    
    # Use Semgrep for JavaScript code analysis
    try:
        semgrep_runner = SemgrepRunner()
        semgrep_findings = semgrep_runner.run(express_app_path)
        findings.extend(semgrep_findings)
    except Exception as e:
        print(f"⚠️ Semgrep scan failed: {e}")
    
    print(f"🔍 Found {len(findings)} potential vulnerabilities")
    
    return {
        "app_name": "Node Express Demo App",
        "app_path": express_app_path,
        "findings": findings,
        "scan_type": "SAST (JavaScript)"
    }

def generate_vulnerability_report(scan_results):
    """Generate a comprehensive vulnerability report"""
    print("\n=== Generating Vulnerability Report ===")
    
    if not scan_results:
        print("❌ No scan results to report")
        return
    
    # Count total vulnerabilities
    total_vulnerabilities = sum(len(result["findings"]) for result in scan_results if result)
    
    print(f"📊 Total vulnerabilities found: {total_vulnerabilities}")
    
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
                severity = finding.get("severity", "medium").lower()
                if severity == "high":
                    report_data["summary"]["high_severity"] += 1
                elif severity == "medium":
                    report_data["summary"]["medium_severity"] += 1
                elif severity == "low":
                    report_data["summary"]["low_severity"] += 1
                
                report_data["findings"].append(finding)
        
        # Save raw JSON data
        with open("demo_apps_vulnerabilities.json", "w") as f:
            json.dump(report_data, f, indent=2)
            
        print(f"✅ Raw vulnerability data saved to demo_apps_vulnerabilities.json")
        
        # Generate HTML report
        report_path = report_generator.generate_report(report_data, format="html")
        print(f"✅ HTML report generated at {report_path}")
        
        return report_path
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return None

def main():
    """Main function to scan demo apps and generate reports"""
    print("=== AutoThreatMap Demo Apps Vulnerability Scanner ===")
    
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
    print(f"📊 Apps scanned: {len(scan_results)}")
    print(f"📄 Report generated: {report_path if report_path else 'Failed'}")
    
    if not scan_results:
        print("❌ No apps were successfully scanned")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Comprehensive test script for AutoThreatMap
Tests all scanners, report generation, and email notifications
"""

import os
import sys
import json
import time
import argparse
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("autothreatmap.test")

# Default settings
DEFAULT_API_URL = "http://localhost:8000"
DEMO_APPS = {
    "python": "./demo-apps/python-flask",
    "node": "./demo-apps/node-express",
    "java": "./demo-apps/java-spring",  # If available
    "go": "./demo-apps/go-gin",         # If available
}

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test AutoThreatMap functionality")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API URL")
    parser.add_argument("--email", help="Email for notifications")
    parser.add_argument("--target-url", default="http://localhost:5000", help="URL for DAST scanning")
    parser.add_argument("--report-format", default="pdf", choices=["pdf", "html"], help="Report format")
    parser.add_argument("--test-all", action="store_true", help="Run all tests")
    parser.add_argument("--test-sast", action="store_true", help="Test SAST scanners")
    parser.add_argument("--test-dast", action="store_true", help="Test DAST scanner")
    parser.add_argument("--test-java", action="store_true", help="Test Java scanner")
    parser.add_argument("--test-go", action="store_true", help="Test Go scanner")
    parser.add_argument("--test-reports", action="store_true", help="Test report generation")
    parser.add_argument("--test-email", action="store_true", help="Test email notifications")
    return parser.parse_args()

def wait_for_scan_completion(api_url, scan_id, timeout=300):
    """Wait for scan to complete with timeout"""
    logger.info(f"Waiting for scan {scan_id} to complete...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{api_url}/api/scan/{scan_id}")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "COMPLETED":
                    logger.info(f"Scan {scan_id} completed successfully")
                    return data
                elif status == "FAILED":
                    logger.error(f"Scan {scan_id} failed: {data.get('error')}")
                    return None
                
                logger.info(f"Scan status: {status}")
            else:
                logger.warning(f"Failed to get scan status: {response.status_code}")
                
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error checking scan status: {str(e)}")
            time.sleep(5)
    
    logger.error(f"Scan {scan_id} timed out after {timeout} seconds")
    return None

def test_sast_scanners(api_url, repo_path, email=None):
    """Test SAST scanners (Semgrep, Bandit, Retire.js)"""
    logger.info(f"Testing SAST scanners on {repo_path}")
    
    # Prepare scan request
    scan_request = {
        "repo_path": os.path.abspath(repo_path),
        "scan_id": f"test-sast-{int(time.time())}",
        "email_notification": bool(email),
        "notification_email": email
    }
    
    # Start scan
    try:
        response = requests.post(f"{api_url}/scan", json=scan_request)
        if response.status_code != 200:
            logger.error(f"Failed to start SAST scan: {response.status_code}")
            return False
            
        scan_id = response.json().get("scan_id")
        logger.info(f"Started SAST scan with ID: {scan_id}")
        
        # Wait for scan completion
        scan_result = wait_for_scan_completion(api_url, scan_id)
        if not scan_result:
            return False
            
        # Verify findings
        findings = scan_result.get("findings", [])
        logger.info(f"Found {len(findings)} issues in SAST scan")
        
        # Check if we have findings from each scanner
        tools = set(finding.get("tool") for finding in findings)
        expected_tools = {"Semgrep", "Bandit", "Retire.js"}
        missing_tools = expected_tools - tools
        
        if missing_tools:
            logger.warning(f"Missing findings from these tools: {missing_tools}")
        
        return len(findings) > 0
        
    except Exception as e:
        logger.error(f"Error during SAST scan: {str(e)}")
        return False

def test_dast_scanner(api_url, repo_path, target_url, email=None):
    """Test DAST scanner (OWASP ZAP)"""
    logger.info(f"Testing DAST scanner on {target_url}")
    
    # Prepare scan request
    scan_request = {
        "repo_path": os.path.abspath(repo_path),
        "scan_id": f"test-dast-{int(time.time())}",
        "include_dast": True,
        "target_url": target_url,
        "email_notification": bool(email),
        "notification_email": email
    }
    
    # Start scan
    try:
        response = requests.post(f"{api_url}/scan", json=scan_request)
        if response.status_code != 200:
            logger.error(f"Failed to start DAST scan: {response.status_code}")
            return False
            
        scan_id = response.json().get("scan_id")
        logger.info(f"Started DAST scan with ID: {scan_id}")
        
        # Wait for scan completion
        scan_result = wait_for_scan_completion(api_url, scan_id)
        if not scan_result:
            return False
            
        # Verify findings
        findings = scan_result.get("findings", [])
        zap_findings = [f for f in findings if f.get("tool") == "ZAP"]
        logger.info(f"Found {len(zap_findings)} issues in DAST scan")
        
        return len(zap_findings) > 0
        
    except Exception as e:
        logger.error(f"Error during DAST scan: {str(e)}")
        return False

def test_language_scanner(api_url, repo_path, language, email=None):
    """Test language-specific scanner"""
    logger.info(f"Testing {language} scanner on {repo_path}")
    
    # Prepare scan request
    scan_request = {
        "repo_path": os.path.abspath(repo_path),
        "scan_id": f"test-{language}-{int(time.time())}",
        "email_notification": bool(email),
        "notification_email": email
    }
    
    # Start scan
    try:
        response = requests.post(f"{api_url}/scan", json=scan_request)
        if response.status_code != 200:
            logger.error(f"Failed to start {language} scan: {response.status_code}")
            return False
            
        scan_id = response.json().get("scan_id")
        logger.info(f"Started {language} scan with ID: {scan_id}")
        
        # Wait for scan completion
        scan_result = wait_for_scan_completion(api_url, scan_id)
        if not scan_result:
            return False
            
        # Verify findings
        findings = scan_result.get("findings", [])
        
        # Check for language-specific findings
        tool_map = {
            "java": "SpotBugs",
            "go": "Gosec"
        }
        
        tool = tool_map.get(language.lower())
        language_findings = [f for f in findings if f.get("tool") == tool]
        logger.info(f"Found {len(language_findings)} issues in {language} scan")
        
        return len(language_findings) > 0
        
    except Exception as e:
        logger.error(f"Error during {language} scan: {str(e)}")
        return False

def test_report_generation(api_url, repo_path, report_format, email=None):
    """Test report generation"""
    logger.info(f"Testing {report_format} report generation")
    
    # Prepare scan request
    scan_request = {
        "repo_path": os.path.abspath(repo_path),
        "scan_id": f"test-report-{int(time.time())}",
        "export_format": report_format,
        "email_notification": bool(email),
        "notification_email": email
    }
    
    # Start scan
    try:
        response = requests.post(f"{api_url}/scan", json=scan_request)
        if response.status_code != 200:
            logger.error(f"Failed to start scan for report: {response.status_code}")
            return False
            
        scan_id = response.json().get("scan_id")
        logger.info(f"Started scan with ID: {scan_id}")
        
        # Wait for scan completion
        scan_result = wait_for_scan_completion(api_url, scan_id)
        if not scan_result:
            return False
            
        # Check for report path
        report_path = scan_result.get("report_path")
        if report_path:
            logger.info(f"Report generated at: {report_path}")
            return True
        else:
            # Try to export report explicitly
            response = requests.post(
                f"{api_url}/api/export/{scan_id}",
                params={"export_format": report_format, "email": email}
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Report generated: {result}")
                return True
            else:
                logger.error(f"Failed to generate report: {response.status_code}")
                return False
        
    except Exception as e:
        logger.error(f"Error during report generation: {str(e)}")
        return False

def test_email_notification(api_url, repo_path, email):
    """Test email notification system"""
    if not email:
        logger.error("Email address required for notification test")
        return False
        
    logger.info(f"Testing email notifications to {email}")
    
    # Prepare scan request with critical vulnerabilities
    scan_request = {
        "repo_path": os.path.abspath(repo_path),
        "scan_id": f"test-email-{int(time.time())}",
        "email_notification": True,
        "notification_email": email
    }
    
    # Start scan
    try:
        response = requests.post(f"{api_url}/scan", json=scan_request)
        if response.status_code != 200:
            logger.error(f"Failed to start scan for email test: {response.status_code}")
            return False
            
        scan_id = response.json().get("scan_id")
        logger.info(f"Started scan with ID: {scan_id}")
        
        # Wait for scan completion
        scan_result = wait_for_scan_completion(api_url, scan_id)
        if not scan_result:
            return False
            
        logger.info(f"Email notification should have been sent to {email}")
        logger.info("Please check your inbox to verify the email was received")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during email notification test: {str(e)}")
        return False

def run_all_tests(args):
    """Run all tests"""
    results = {}
    
    # Test SAST scanners
    if args.test_all or args.test_sast:
        results["sast"] = test_sast_scanners(
            args.api_url, 
            DEMO_APPS["python"], 
            args.email
        )
    
    # Test DAST scanner
    if args.test_all or args.test_dast:
        results["dast"] = test_dast_scanner(
            args.api_url, 
            DEMO_APPS["python"], 
            args.target_url, 
            args.email
        )
    
    # Test Java scanner
    if (args.test_all or args.test_java) and "java" in DEMO_APPS:
        results["java"] = test_language_scanner(
            args.api_url, 
            DEMO_APPS["java"], 
            "java", 
            args.email
        )
    
    # Test Go scanner
    if (args.test_all or args.test_go) and "go" in DEMO_APPS:
        results["go"] = test_language_scanner(
            args.api_url, 
            DEMO_APPS["go"], 
            "go", 
            args.email
        )
    
    # Test report generation
    if args.test_all or args.test_reports:
        results["reports"] = test_report_generation(
            args.api_url, 
            DEMO_APPS["python"], 
            args.report_format, 
            args.email
        )
    
    # Test email notifications
    if (args.test_all or args.test_email) and args.email:
        results["email"] = test_email_notification(
            args.api_url, 
            DEMO_APPS["python"], 
            args.email
        )
    
    return results

def main():
    """Main function"""
    args = parse_args()
    
    # Check if any test is selected
    if not (args.test_all or args.test_sast or args.test_dast or 
            args.test_java or args.test_go or args.test_reports or args.test_email):
        args.test_all = True
    
    # Run tests
    logger.info("Starting AutoThreatMap tests")
    results = run_all_tests(args)
    
    # Print results
    logger.info("\n--- Test Results ---")
    all_passed = True
    for test, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test.upper()}: {status}")
        all_passed = all_passed and passed
    
    # Exit with appropriate code
    if all_passed:
        logger.info("All tests passed!")
        return 0
    else:
        logger.error("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
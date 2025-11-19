#!/usr/bin/env python3
"""
Quick test script for ThreatModelerX enhancements
"""
import os
import sys
import importlib.util
import json
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_module_import(module_path, class_name):
    """Test if a module can be imported"""
    try:
        # Try to import the module
        module_name = module_path.replace("/", ".").replace("\\", ".")
        if module_name.startswith("backend."):
            module_name = module_name[8:]  # Remove 'backend.' prefix
        
        print(f"Attempting to import {module_name}")
        module = __import__(module_name, fromlist=[class_name])
        
        # Check if the class exists in the module
        if hasattr(module, class_name):
            print(f"[PASS] {class_name} module imported successfully")
            return True, module
        else:
            print(f"[FAIL] {class_name} class not found in module")
            return False, None
    except ImportError as e:
        print(f"[FAIL] {class_name} test failed: {str(e)}")
        return False, None
    except Exception as e:
        print(f"[FAIL] {class_name} test failed with unexpected error: {str(e)}")
        return False, None

def test_email_notifier():
    """Test EmailNotifier functionality"""
    success, module = test_module_import("app.workers.email_notifier", "EmailNotifier")
    if not success:
        return False
    
    try:
        # Create an instance with test parameters
        notifier = module.EmailNotifier(
            smtp_server="test.example.com",
            smtp_port=587,
            smtp_username="test",
            smtp_password="test",
            sender_email="test@example.com"
        )
        print("[PASS] Email Notifier instance created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Email Notifier instantiation failed: {str(e)}")
        return False

def mock_pdfkit():
    """Mock pdfkit module if not available"""
    try:
        import pdfkit
        return True
    except ImportError:
        print("[WARN] pdfkit not available, using mock implementation")
        import sys
        class MockPdfKit:
            @staticmethod
            def from_string(html, output_path, options=None):
                print(f"Mock: Converting HTML to PDF at {output_path}")
                with open(output_path, 'w') as f:
                    f.write("Mock PDF content")
                return True
        
        sys.modules['pdfkit'] = MockPdfKit()
        return True

def mock_aiohttp():
    """Mock aiohttp module if not available"""
    try:
        import aiohttp
        return True
    except ImportError:
        print("[WARN] aiohttp not available, using mock implementation")
        import sys
        class MockClientSession:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            async def get(self, url, **kwargs):
                return MockResponse()
                
            async def post(self, url, **kwargs):
                return MockResponse()
                
            async def close(self):
                pass
        
        class MockResponse:
            async def json(self):
                return {"status": "success", "data": {}}
                
            async def text(self):
                return "Mock response text"
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
            @property
            def status(self):
                return 200
        
        class MockAiohttp:
            ClientSession = MockClientSession
        
        sys.modules['aiohttp'] = MockAiohttp
        return True

def test_report_generator():
    """Test ReportGenerator functionality without pdfkit dependency"""
    try:
        # Mock dependencies
        mock_pdfkit()
        
        from app.workers.report_generator import ReportGenerator
        print("[PASS] Report Generator module imported successfully")
        
        # Create a simple test template directory
        os.makedirs("temp/templates", exist_ok=True)
        with open("temp/templates/report.html", "w") as f:
            f.write("<html><body><h1>Test Report</h1></body></html>")
        
        # Create an instance with test parameters
        generator = ReportGenerator(templates_dir="temp/templates")
        print("[PASS] Report Generator instance created successfully")
        
        # Clean up
        os.remove("temp/templates/report.html")
        os.rmdir("temp/templates")
        os.rmdir("temp")
        return True
    except Exception as e:
        print(f"[FAIL] Report Generator test failed: {str(e)}")
        # Clean up in case of failure
        if os.path.exists("temp/templates/report.html"):
            os.remove("temp/templates/report.html")
        if os.path.exists("temp/templates"):
            os.rmdir("temp/templates")
        if os.path.exists("temp"):
            os.rmdir("temp")
        return False

def test_model_updates():
    """Test if ScanRequest model has been updated with new fields"""
    try:
        from app.models import ScanRequest
        
        # Create a test instance with all required fields
        scan_request = ScanRequest(
            repo_path="test_repo",
            target_url="https://example.com",
            include_dast=True,
            email_notification=True,
            notification_email="test@example.com"
        )
        
        # Check if fields exist and have correct values
        if (hasattr(scan_request, "target_url") and 
            hasattr(scan_request, "notification_email") and
            hasattr(scan_request, "include_dast") and
            hasattr(scan_request, "email_notification")):
            print("[PASS] ScanRequest model has been updated with new fields")
            return True
        else:
            print("[FAIL] ScanRequest model is missing required fields")
            return False
    except Exception as e:
        print(f"[FAIL] Model updates test failed: {str(e)}")
        return False

def test_zap_runner():
    """Test ZapRunner functionality"""
    try:
        # Mock dependencies
        mock_aiohttp()
        
        # Create a mock for python-zaproxy
        try:
            import zapv2
        except ImportError:
            print("[WARN] zapv2 not available, using mock implementation")
            import sys
            
            class MockZAPv2:
                def __init__(self, proxies=None, apikey=None):
                    self.core = MockZAPComponent()
                    self.spider = MockZAPComponent()
                    self.ascan = MockZAPComponent()
                    self.alerts = MockZAPComponent()
                
            class MockZAPComponent:
                def status(self, scanid=None):
                    return "100"
                    
                def scan(self, url, **kwargs):
                    return "1"
                    
                def alerts(self, **kwargs):
                    return [{"alert": "XSS", "risk": "High", "cweId": "79"}]
                    
                def shutdown(self):
                    return True
                    
                def new_session(self, **kwargs):
                    return True
            
            sys.modules['zapv2'] = MockZAPv2
        
        from app.scanner.zap_runner import ZapRunner
        print("[PASS] ZAP Runner module imported successfully")
        
        # Create an instance with test parameters
        runner = ZapRunner(zap_api_url="http://localhost:8080", api_key="test_key")
        print("[PASS] ZAP Runner instance created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] ZAP Runner test failed: {str(e)}")
        return False

def test_spotbugs_runner():
    """Test SpotBugsRunner functionality"""
    try:
        from app.scanner.spotbugs_runner import SpotBugsRunner
        print("[PASS] SpotBugs Runner module imported successfully")
        
        # Create an instance with test parameters
        runner = SpotBugsRunner(spotbugs_path="/usr/local/bin/spotbugs")
        print("[PASS] SpotBugs Runner instance created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] SpotBugs Runner test failed: {str(e)}")
        return False

def test_gosec_runner():
    """Test GosecRunner functionality"""
    try:
        from app.scanner.gosec_runner import GosecRunner
        print("[PASS] Gosec Runner module imported successfully")
        
        # Create an instance with test parameters
        runner = GosecRunner(gosec_path="/usr/local/bin/gosec")
        print("[PASS] Gosec Runner instance created successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Gosec Runner test failed: {str(e)}")
        return False

def test_demo_apps():
    """Test demo applications for vulnerabilities"""
    try:
        # Check if demo apps exist
        demo_path = Path(__file__).parent / "demo-apps"
        if not demo_path.exists():
            print("[FAIL] Demo apps directory not found")
            return False
        
        # Check Python Flask demo
        flask_demo = demo_path / "python-flask"
        if flask_demo.exists() and (flask_demo / "app.py").exists():
            print("[PASS] Python Flask demo app found")
        else:
            print("[FAIL] Python Flask demo app not found")
            return False
        
        # Check Node Express demo
        node_demo = demo_path / "node-express"
        if node_demo.exists() and (node_demo / "app.js").exists():
            print("[PASS] Node Express demo app found")
        else:
            print("[FAIL] Node Express demo app not found")
            return False
        
        print("[PASS] Demo apps verified successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Demo apps test failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("\n=== Testing ThreatModelerX Enhancements ===\n")
    
    # Test results
    results = {
        "Email Notifications": test_email_notifier(),
        "Report Generation": test_report_generator(),
        "Model Updates": test_model_updates(),
        "DAST Integration (ZAP)": test_zap_runner(),
        "Java Scanner (SpotBugs)": test_spotbugs_runner(),
        "Go Scanner (gosec)": test_gosec_runner(),
        "Demo Apps": test_demo_apps()
    }
    
    # Print summary
    print("\n=== Test Results Summary ===\n")
    
    all_passed = True
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n[PASS] All tests passed!")
    else:
        print("\n[FAIL] Some tests failed. Please check the logs above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
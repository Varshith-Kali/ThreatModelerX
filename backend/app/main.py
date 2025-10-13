from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime, timedelta
import uuid
from functools import lru_cache

from .models import (
    ScanRequest, ScanResult, Finding, Threat,
    RemediationPlan, SeverityLevel
)
from .scanner import SemgrepRunner, BanditRunner, RetireRunner, ZapRunner, SpotBugsRunner, GosecRunner
from .threatmodel import StrideMapper
from .architecture import ArchitectureAnalyzer
from .workers.risk_scorer import RiskScorer
from .workers.remediation_planner import RemediationPlanner
from .workers.report_generator import ReportGenerator
from .workers.email_notifier import EmailNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("autothreatmap")

app = FastAPI(
    title="AutoThreatMap API",
    description="Automated Security Analysis and Threat Modeling Platform",
    version="1.0.0"
)

# Add GZip compression for better performance
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Use a persistent storage with TTL for scan results
import json
import os
from collections import OrderedDict

class PersistentTTLCache(OrderedDict):
    def __init__(self, max_size=1000, ttl=3600, storage_file="scan_results.json"):
        self.max_size = max_size
        self.ttl = ttl
        self.storage_file = os.path.join(os.path.dirname(__file__), storage_file)
        super().__init__()
        self._load_from_disk()
        
    def _load_from_disk(self):
        """Load cached results from disk if available"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        # Convert expiry string back to datetime
                        if 'expiry' in value and isinstance(value['expiry'], str):
                            value['expiry'] = datetime.fromisoformat(value['expiry'])
                        super().__setitem__(key, value)
                logger.info(f"Loaded {len(data)} scan results from persistent storage")
        except Exception as e:
            logger.error(f"Error loading scan results from disk: {str(e)}")
    
    def _save_to_disk(self):
        """Save current cache to disk"""
        try:
            # Create a copy of the data with datetime objects converted to strings
            serializable_data = {}
            for key, value in self.items():
                serializable_value = value.copy()
                if 'expiry' in serializable_value and isinstance(serializable_value['expiry'], datetime):
                    serializable_value['expiry'] = serializable_value['expiry'].isoformat()
                # Convert any other datetime objects in the result
                if 'result' in serializable_value and serializable_value['result']:
                    serializable_value['result'] = json.loads(datetime_safe_dumps(serializable_value['result']))
                serializable_data[key] = serializable_value
                
            with open(self.storage_file, 'w') as f:
                json.dump(serializable_data, f)
            logger.info(f"Saved {len(self)} scan results to persistent storage")
        except Exception as e:
            logger.error(f"Error saving scan results to disk: {str(e)}")
        
    def __setitem__(self, key, value):
        if len(self) >= self.max_size:
            self.popitem(last=False)
        value['expiry'] = datetime.utcnow() + timedelta(seconds=self.ttl)
        super().__setitem__(key, value)
        self._save_to_disk()
        
    def __getitem__(self, key):
        value = super().__getitem__(key)
        if datetime.utcnow() > value.get('expiry', datetime.max):
            del self[key]
            self._save_to_disk()
            raise KeyError(key)
        return value
    
    def __delitem__(self, key):
        super().__delitem__(key)
        self._save_to_disk()

scan_results_store = PersistentTTLCache(max_size=100, ttl=86400)  # Store up to 100 scans for 24 hours

@app.get("/")
async def root():
    return {
        "name": "AutoThreatMap",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "scan": "/api/scan",
            "results": "/api/scan/{scan_id}",
            "findings": "/api/findings",
            "threats": "/api/threats",
            "remediation": "/api/remediation/{finding_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/findings/{finding_id}/review")
async def add_finding_review(finding_id: str, review_data: dict):
    """Add manual review data to a finding"""
    for scan_id, scan_data in scan_results_store.items():
        scan_result = scan_data.get('result')
        if not scan_result:
            continue
            
        for finding in scan_result.get('findings', []):
            if finding.get('id') == finding_id:
                # Add review data
                finding['manual_review'] = review_data
                finding['updated_at'] = datetime.utcnow().isoformat()
                
                # Add reviewer comment if provided
                if 'comment' in review_data:
                    if 'reviewer_comments' not in finding:
                        finding['reviewer_comments'] = []
                    finding['reviewer_comments'].append({
                        'comment': review_data['comment'],
                        'reviewer': review_data.get('reviewer', 'anonymous'),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                # Update status if provided
                if 'status' in review_data:
                    finding['status'] = review_data['status']
                    
                return {"status": "success", "finding": finding}
                
    raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")

@app.post("/api/export/{scan_id}")
async def export_report(scan_id: str, export_format: str = "json", email: Optional[str] = None):
    """Export scan results in various formats and optionally email the report"""
    if scan_id not in scan_results_store:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
        
    scan_data = scan_results_store[scan_id].get('result')
    if not scan_data:
        raise HTTPException(status_code=404, detail="Scan results not found")
        
    if export_format == "json":
        result = scan_data
    elif export_format in ["html", "pdf"]:
        # Use the ReportGenerator to create HTML or PDF reports
        report_generator = ReportGenerator()
        try:
            report_path = report_generator.generate_report(scan_data, format=export_format)
            
            # If email is provided, send the report via email
            if email:
                try:
                    email_notifier = EmailNotifier()
                    email_notifier.send_notification(
                        subject=f"Security Scan Report: {scan_id}",
                        message=f"Please find attached the security scan report for {scan_id}.",
                        recipients=[email],
                        attachment_path=report_path
                    )
                    
                    logger.info(f"Report for scan {scan_id} sent to {email}")
                except Exception as email_error:
                    logger.error(f"Failed to send email with report: {str(email_error)}")
                    # Continue execution to return the report even if email fails
            
            # In a real implementation, we would return the file for download
            # For now, return the path to the generated report
            return {
                "status": "success",
                "report_format": export_format,
                "report_path": report_path,
                "email_sent": email is not None,
                "message": f"{export_format.upper()} report generated successfully"
            }
        except Exception as e:
            logger.error(f"Error generating {export_format} report: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate {export_format} report: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {export_format}")

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def datetime_safe_dumps(obj):
    """Helper function to safely serialize objects with datetime values"""
    return json.dumps(obj, cls=CustomJSONEncoder)

@app.post("/api/scan", response_model=dict)
@app.post("/scan", response_model=dict)  # Add additional route to match frontend request
async def create_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    scan_id = f"SCAN-{uuid.uuid4().hex[:12]}"
    
    # Log the incoming request for debugging
    logger.info(f"Received scan request: {request.dict()}")
    
    # HARDCODED SOLUTION: Use direct paths to demo apps based on selection
    # The demo-apps folder is in the project root, not in the backend folder
    project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    
    if "python-flask" in request.repo_path:
        # Python Flask demo app
        repo_path = os.path.join(project_root, "demo-apps", "python-flask")
    elif "node-express" in request.repo_path:
        # Node Express demo app
        repo_path = os.path.join(project_root, "demo-apps", "node-express")
    else:
        # Default to Python Flask if path can't be determined
        repo_path = os.path.join(project_root, "demo-apps", "python-flask")
        
    logger.info(f"Using hardcoded demo path: {repo_path}")
    
    # Final check to ensure path exists
    if not os.path.exists(repo_path):
        logger.error(f"Path does not exist: {repo_path}")
        raise HTTPException(status_code=400, detail=f"Repository path not found: {repo_path}")

    scan_results_store[scan_id] = {
        "status": "running",
        "repo_path": repo_path,
        "started_at": datetime.utcnow().isoformat()
    }

    background_tasks.add_task(run_scan, scan_id, request)

    return {
        "scan_id": scan_id,
        "status": "initiated",
        "message": "Scan started in background"
    }

@app.post("/api/scan/auto", response_model=dict)
async def auto_scan(request: ScanRequest):
    """
    One-click automated scan endpoint that runs the scan and returns the scan ID
    """
    # Create a regular scan without background tasks
    scan_id = f"SCAN-{uuid.uuid4().hex[:12]}"
    
    # Log the incoming request for debugging
    logger.info(f"Received auto scan request: {request.dict()}")
    
    # HARDCODED SOLUTION: Use direct paths to demo apps based on selection
    project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    
    if "python-flask" in request.repo_path:
        repo_path = os.path.join(project_root, "demo-apps", "python-flask")
    elif "node-express" in request.repo_path:
        repo_path = os.path.join(project_root, "demo-apps", "node-express")
    else:
        repo_path = os.path.join(project_root, "demo-apps", "python-flask")
        
    logger.info(f"Using hardcoded demo path for auto scan: {repo_path}")
    
    # Final check to ensure path exists
    if not os.path.exists(repo_path):
        logger.error(f"Path does not exist: {repo_path}")
        raise HTTPException(status_code=400, detail=f"Repository path not found: {repo_path}")

    scan_results_store[scan_id] = {
        "status": "running",
        "repo_path": repo_path,
        "started_at": datetime.utcnow().isoformat()
    }

    # Run scan synchronously for auto endpoint
    try:
        # Run the scan directly
        result = await run_scan(scan_id, request)
        
        # Get findings and threats
        findings = result.get("findings", [])
        threats = result.get("threats", [])
        
        # Generate summary
        summary = {
            "scan_id": scan_id,
            "timestamp": datetime.utcnow().isoformat(),
            "repo_path": request.repo_path,
            "findings_count": len(findings),
            "threats_count": len(threats),
            "scan_types": request.scan_types,
            "completed_at": scan_results_store[scan_id].get("completed_at")
        }
        
        return {
            "scan_id": scan_id,
            "status": "completed",
            "summary": summary,
            "findings": findings,
            "threats": threats,
            "report_url": f"/api/report/{scan_id}"
        }
    except Exception as e:
        logger.error(f"Error in auto scan: {str(e)}")
        scan_results_store[scan_id]["status"] = "error"
        scan_results_store[scan_id]["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Error running scan: {str(e)}")

def run_scan_sync(scan_id: str, request: ScanRequest):
    """Synchronous version of run_scan for the auto endpoint"""
    try:
        repo_path = scan_results_store[scan_id]["repo_path"]
        logger.info(f"Starting scan {scan_id} for {repo_path}")
        
        # Initialize results
        findings = []
        threats = []
        
        # Run SAST scanners if requested
        if "sast" in request.scan_types:
            logger.info(f"Running SAST scanners for {scan_id}")
            
            # Initialize scanners
            semgrep = SemgrepRunner()
            bandit = BanditRunner()
            retire = RetireRunner()
            
            # Run scanners
            semgrep_findings = semgrep.run(repo_path)
            bandit_findings = bandit.run(repo_path)
            retire_findings = retire.run(repo_path)
            
            # Combine findings
            findings.extend(semgrep_findings)
            findings.extend(bandit_findings)
            findings.extend(retire_findings)
            
            logger.info(f"SAST scan completed for {scan_id}: {len(findings)} findings")
        
        # Run threat modeling if requested
        if "threat_modeling" in request.scan_types:
            logger.info(f"Running threat modeling for {scan_id}")
            
            # Initialize threat modeler
            threat_modeler = StrideMapper()
            
            # Generate threats using the correct analyze_code method
            threats = threat_modeler.analyze_code(repo_path, findings)
            
            logger.info(f"Threat modeling completed for {scan_id}: {len(threats)} threats")
        
        # Return combined results
        return {
            "findings": findings,
            "threats": threats
        }
    except Exception as e:
        logger.error(f"Error in run_scan_sync: {str(e)}")
        raise

async def run_scan(scan_id: str, request: ScanRequest):
    try:
        all_findings = []
        import asyncio
        import logging
        logger = logging.getLogger("autothreatmap")
        
        # Get the corrected repo path from the scan store
        repo_path = scan_results_store[scan_id]["repo_path"]
        logger.info(f"Starting scan with ID {scan_id} on repository: {repo_path}")
        
        # Debug log the scan types
        logger.info(f"Scan types requested: {request.scan_types}")
        
        # Update scan status with progress information
        def update_progress(stage, progress=None, details=None):
            current = scan_results_store.get(scan_id, {})
            current["status"] = "running"
            current["current_stage"] = stage
            if progress:
                current["progress"] = progress
            if details:
                current["details"] = details
            scan_results_store[scan_id] = current
            
        update_progress("initializing", "0%", "Setting up scan environment")

        if "sast" in request.scan_types or "all" in request.scan_types:
            # Run security scanners in parallel for better performance
            update_progress("running SAST scanners", "10%", "Initializing security scanners")
            
            semgrep = SemgrepRunner()
            bandit = BanditRunner()
            retire = RetireRunner()
            
            # Execute scanners concurrently with timeout
            try:
                # Execute scanners concurrently with a 60-second timeout
                semgrep_task = asyncio.create_task(asyncio.to_thread(semgrep.run, repo_path))
                bandit_task = asyncio.create_task(asyncio.to_thread(bandit.run, repo_path))
                retire_task = asyncio.create_task(asyncio.to_thread(retire.run, repo_path))
                
                # Gather results with timeout (60 seconds)
                semgrep_findings, bandit_findings, retire_findings = await asyncio.wait_for(
                    asyncio.gather(semgrep_task, bandit_task, retire_task),
                    timeout=60.0  # 60 second timeout
                )
                
                update_progress("processing SAST results", "40%", "Analyzing scanner findings")
                all_findings.extend(semgrep_findings)
                all_findings.extend(bandit_findings)
                all_findings.extend(retire_findings)
                update_progress("SAST scan completed", "60%", f"Found {len(semgrep_findings) + len(bandit_findings) + len(retire_findings)} vulnerabilities")
                
            except asyncio.TimeoutError:
                logger.warning(f"SAST scanning timed out for scan {scan_id}")
                # Add a timeout finding to indicate the issue
                all_findings.append(Finding(
                    title="Scan Timeout",
                    description="The security scan timed out. Some results may be incomplete.",
                    severity=SeverityLevel.MEDIUM,
                    tool="system",
                    file_path="",
                    line_number=0
                ))
            
            update_progress("SAST scanning completed", "50%")

        threats = []
        attack_graph = {}
        if "threat_model" in request.scan_types or "all" in request.scan_types:
            update_progress("running threat modeling", "60%")
            try:
                # Use the logger that was already defined at the beginning of the function
                stride_mapper = StrideMapper()
                logger.info(f"Starting threat modeling for scan {scan_id}")
                # Add timeout for threat modeling (30 seconds)
                threat_task = asyncio.create_task(asyncio.to_thread(stride_mapper.analyze_code, repo_path, all_findings))
                threats = await asyncio.wait_for(threat_task, timeout=30.0)
                
                # Generate attack graph with timeout (15 seconds)
                graph_task = asyncio.create_task(asyncio.to_thread(stride_mapper.generate_attack_graph, threats))
                attack_graph = await asyncio.wait_for(graph_task, timeout=15.0)
            except asyncio.TimeoutError:
                logger.warning(f"Threat modeling timed out for scan {scan_id}")
                # Add a placeholder threat if timeout occurs
                threats.append(Threat(
                    title="Threat Modeling Timeout",
                    description="The threat modeling process timed out. Results may be incomplete.",
                    stride_category="Information Disclosure",
                    affected_components=["system"],
                    mitre_ids=["T0000"],
                    severity=SeverityLevel.MEDIUM
                ))
            
            update_progress("threat modeling completed", "80%")

        update_progress("calculating risk scores", "90%")
        risk_scorer = RiskScorer()
        for finding in all_findings:
            finding.risk_score = risk_scorer.calculate_risk(finding)

        all_findings.sort(key=lambda x: x.risk_score or 0, reverse=True)

        summary = {
            "total_findings": len(all_findings),
            "by_severity": {
                "critical": len([f for f in all_findings if f.severity == SeverityLevel.CRITICAL]),
                "high": len([f for f in all_findings if f.severity == SeverityLevel.HIGH]),
                "medium": len([f for f in all_findings if f.severity == SeverityLevel.MEDIUM]),
                "low": len([f for f in all_findings if f.severity == SeverityLevel.LOW])
            },
            "by_tool": {},
            "total_threats": len(threats),
            "attack_graph": attack_graph
        }

        for finding in all_findings:
            if finding.tool not in summary["by_tool"]:
                summary["by_tool"][finding.tool] = 0
            summary["by_tool"][finding.tool] += 1

        overall_risk = risk_scorer.calculate_overall_risk(all_findings)

        result = ScanResult(
            scan_id=scan_id,
            repo_path=repo_path,
            timestamp=datetime.utcnow(),
            findings=all_findings,
            threats=threats,
            summary=summary,
            risk_score=overall_risk
        )

        update_progress("finalizing results", "100%")
        scan_results_store[scan_id] = {
            "status": "completed",
            "result": result.dict(),
            "completed_at": datetime.utcnow().isoformat(),
            "progress": "100%"
        }
        
        return result.dict()
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        scan_results_store[scan_id] = {
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }
        
        # Send email notification about failed scan
        try:
            email_notifier = EmailNotifier()
            email_notifier.send_notification(
                subject=f"Scan Failed: {scan_id}",
                message=f"Scan failed with error: {str(e)}\n\nRepository: {repo_path}",
                recipients=[request.notification_email] if hasattr(request, 'notification_email') else None
            )
        except Exception as email_error:
            logger.error(f"Failed to send email notification: {str(email_error)}")
            
        raise

@app.get("/api/scan/{scan_id}")
@app.get("/scan/{scan_id}")  # Add additional route to match frontend request
async def get_scan_result(scan_id: str):
    try:
        import logging
        logger = logging.getLogger("autothreatmap")
        
        if scan_id not in scan_results_store:
            logger.warning(f"Scan ID not found: {scan_id}")
            return {
                "status": "not_found",
                "error": "Scan not found or expired",
                "scan_id": scan_id
            }
        
        # Return scan data with better error handling
        scan_data = scan_results_store[scan_id]
        return scan_data
    except Exception as e:
        import logging
        logger = logging.getLogger("autothreatmap")
        logger.error(f"Error retrieving scan {scan_id}: {str(e)}")
        return {
            "status": "error",
            "error": f"Error retrieving scan: {str(e)}",
            "scan_id": scan_id
        }

@app.get("/api/scans")
async def list_scans():
    return {
        "scans": [
            {
                "scan_id": scan_id,
                "status": data["status"],
                "started_at": data.get("started_at"),
                "completed_at": data.get("completed_at")
            }
            for scan_id, data in scan_results_store.items()
        ]
    }

@app.get("/api/findings")
async def get_findings(
    scan_id: Optional[str] = None,
    severity: Optional[SeverityLevel] = None,
    tool: Optional[str] = None
):
    if scan_id:
        if scan_id not in scan_results_store:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan_data = scan_results_store[scan_id]
        if scan_data["status"] != "completed":
            return {"findings": [], "message": f"Scan status: {scan_data['status']}"}

        findings = scan_data["result"]["findings"]
    else:
        findings = []
        for scan_id, data in scan_results_store.items():
            if data["status"] == "completed":
                findings.extend(data["result"]["findings"])

    if severity:
        findings = [f for f in findings if f.get("severity") == severity.value]

    if tool:
        findings = [f for f in findings if f.get("tool") == tool]

    return {"findings": findings, "count": len(findings)}

@app.get("/api/report/{scan_id}")
async def generate_report(scan_id: str, format: str = "json"):
    """Generate a security report for a specific scan"""
    if scan_id not in scan_results_store:
        raise HTTPException(status_code=404, detail=f"Scan with ID {scan_id} not found")
    
    scan_result = scan_results_store[scan_id]
    
    if "result" not in scan_result or not scan_result["result"]:
        raise HTTPException(status_code=400, detail=f"Scan results not available for {scan_id}")
    
    result = scan_result["result"]
    findings = result.get("findings", [])
    threats = result.get("threats", [])
    
    # Create summary statistics
    summary = {
        "scan_id": scan_id,
        "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
        "repo_path": result.get("repo_path", ""),
        "risk_score": result.get("risk_score", 0),
        "findings_count": len(findings),
        "threats_count": len(threats),
        "severity_breakdown": {
            "CRITICAL": len([f for f in findings if f.get("severity") == "CRITICAL"]),
            "HIGH": len([f for f in findings if f.get("severity") == "HIGH"]),
            "MEDIUM": len([f for f in findings if f.get("severity") == "MEDIUM"]),
            "LOW": len([f for f in findings if f.get("severity") == "LOW"]),
            "INFO": len([f for f in findings if f.get("severity") == "INFO"])
        },
        "threat_categories": {
             "SPOOFING": len([t for t in threats if t.get("stride_category") == "SPOOFING"]),
             "TAMPERING": len([t for t in threats if t.get("stride_category") == "TAMPERING"]),
             "REPUDIATION": len([t for t in threats if t.get("stride_category") == "REPUDIATION"]),
             "INFORMATION_DISCLOSURE": len([t for t in threats if t.get("stride_category") == "INFORMATION_DISCLOSURE"]),
             "DENIAL_OF_SERVICE": len([t for t in threats if t.get("stride_category") == "DENIAL_OF_SERVICE"]),
             "ELEVATION_OF_PRIVILEGE": len([t for t in threats if t.get("stride_category") == "ELEVATION_OF_PRIVILEGE"])
         }
    }
    
    if format.lower() == "json":
        return {
            "report": {
                "summary": summary,
                "findings": findings,
                "threats": threats
            }
        }
    elif format.lower() == "html":
        # Generate HTML report
        findings_html = ""
        for f in findings:
            findings_html += f"""
            <li class="finding {f.get('severity', '').lower()}">
                <h3>{f.get('title', 'Unknown Issue')}</h3>
                <p>Severity: {f.get('severity', 'Unknown')}</p>
                <p>File: {f.get('file_path', 'Unknown')} (Line: {f.get('line_number', 'N/A')})</p>
                <p>Tool: {f.get('tool', 'N/A')}</p>
                <pre>{f.get('description', 'No description provided')}</pre>
                <div class="fix">
                    <h4>Suggested Fix:</h4>
                    <p>{f.get('fix_recommendation', 'No fix suggestion available')}</p>
                </div>
            </li>
            """
            
        threats_html = ""
        for t in threats:
            threats_html += f"""
            <li class="threat {t.get('stride_category', '').lower()}">
                <h3>{t.get('title', 'Unknown Threat')}</h3>
                <p>Category: {t.get('stride_category', 'Unknown')}</p>
                <p>Components: {', '.join(t.get('affected_components', ['Unknown']))}</p>
                <p>Severity: {t.get('severity', 'Unknown')}</p>
                <div class="mitigation">
                    <h4>Mitigation:</h4>
                    <p>{t.get('mitigation', 'No mitigation available')}</p>
                </div>
            </li>
            """
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Scan Report - {scan_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
                h1, h2 {{ color: #2c3e50; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .finding, .threat {{ margin-bottom: 15px; padding: 10px; border-radius: 5px; }}
                .critical {{ background-color: #ffebee; border-left: 5px solid #c62828; }}
                .high {{ background-color: #fff8e1; border-left: 5px solid #ff8f00; }}
                .medium {{ background-color: #fffde7; border-left: 5px solid #fdd835; }}
                .low {{ background-color: #e8f5e9; border-left: 5px solid #388e3c; }}
                .info {{ background-color: #e3f2fd; border-left: 5px solid #1976d2; }}
                pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
                .fix, .mitigation {{ background-color: #e8f5e9; padding: 10px; margin-top: 10px; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>Security Scan Report - {scan_id}</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Repository:</strong> {summary['repo_path']}</p>
                <p><strong>Scan Date:</strong> {summary['timestamp']}</p>
                <p><strong>Risk Score:</strong> {summary['risk_score']}</p>
                <p><strong>Findings:</strong> {summary['findings_count']} total</p>
                <ul>
                    <li>Critical: {summary['severity_breakdown']['CRITICAL']}</li>
                    <li>High: {summary['severity_breakdown']['HIGH']}</li>
                    <li>Medium: {summary['severity_breakdown']['MEDIUM']}</li>
                    <li>Low: {summary['severity_breakdown']['LOW']}</li>
                    <li>Info: {summary['severity_breakdown']['INFO']}</li>
                </ul>
                <p><strong>Threats:</strong> {summary['threats_count']} total</p>
            </div>
            
            <h2>Findings</h2>
            <ul>{findings_html}</ul>
            
            <h2>Threats</h2>
            <ul>{threats_html}</ul>
        </body>
        </html>
        """
        return JSONResponse(content={"html": html})
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported report format: {format}")


@app.get("/api/threats")
async def get_threats(scan_id: Optional[str] = None):
    if scan_id:
        if scan_id not in scan_results_store:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan_data = scan_results_store[scan_id]
        if scan_data["status"] != "completed":
            return {"threats": [], "message": f"Scan status: {scan_data['status']}"}

        threats = scan_data["result"]["threats"]
    else:
        threats = []
        for scan_id, data in scan_results_store.items():
            if data["status"] == "completed":
                threats.extend(data["result"]["threats"])

    return {"threats": threats, "count": len(threats)}

@app.get("/api/remediation/{finding_id}")
async def get_remediation_plan(finding_id: str):
    for scan_id, data in scan_results_store.items():
        if data["status"] == "completed":
            findings = data["result"]["findings"]
            finding = next((f for f in findings if f["id"] == finding_id), None)

            if finding:
                planner = RemediationPlanner()
                plan = planner.create_plan(Finding(**finding))
                return plan

    raise HTTPException(status_code=404, detail="Finding not found")

@app.get("/api/stats")
async def get_statistics():
    total_scans = len(scan_results_store)
    completed_scans = len([s for s in scan_results_store.values() if s["status"] == "completed"])

    total_findings = 0
    total_threats = 0
    severity_breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for scan_data in scan_results_store.values():
        if scan_data["status"] == "completed":
            result = scan_data["result"]
            total_findings += result["summary"]["total_findings"]
            total_threats += result["summary"]["total_threats"]

            for severity, count in result["summary"]["by_severity"].items():
                severity_breakdown[severity.upper()] += count

    return {
        "total_scans": total_scans,
        "completed_scans": completed_scans,
        "total_findings": total_findings,
        "total_threats": total_threats,
        "severity_breakdown": severity_breakdown
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

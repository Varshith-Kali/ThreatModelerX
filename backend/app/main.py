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
import shutil
import zipfile
from fastapi import UploadFile, File

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("threatmodelx")

app = FastAPI(
    title="ThreatModelerX API",
    description="Automated Security Analysis and Threat Modeling Platform",
    version="1.0.0"
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = datetime.utcnow()
    response = await call_next(request)
    process_time = (datetime.utcnow() - start_time).total_seconds()
    response.headers["X-Process-Time"] = str(process_time)
    return response

import json
import os
from collections import OrderedDict

import sqlite3
import json
from datetime import datetime, timedelta

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def datetime_safe_dumps(obj):
    """Helper function to safely serialize objects with datetime values"""
    return json.dumps(obj, cls=CustomJSONEncoder)

class SQLiteScanStore:
    def __init__(self, db_file="scan_results.db", ttl=2592000):  # 30 days TTL instead of 1 day
        self.db_file = os.path.join(os.path.dirname(__file__), db_file)
        self.ttl = ttl
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id TEXT PRIMARY KEY,
                    data TEXT,
                    expiry TIMESTAMP
                )
            """)
            conn.commit()

    def __setitem__(self, key, value):
        expiry = datetime.utcnow() + timedelta(seconds=self.ttl)
        # Serialize value, handling datetime objects
        serialized_value = json.dumps(value, cls=CustomJSONEncoder)
        
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO scans (scan_id, data, expiry) VALUES (?, ?, ?)",
                (key, serialized_value, expiry)
            )
            conn.commit()

    def __getitem__(self, key):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute("SELECT data, expiry FROM scans WHERE scan_id = ?", (key,))
                row = cursor.fetchone()
                
                if not row:
                    raise KeyError(key)
                    
                data_str, expiry_str = row
                # Don't check expiry - keep all data permanently unless manually deleted
                # This prevents data loss during active usage
                    
                return json.loads(data_str)
        except sqlite3.Error as e:
            logger.error(f"Database error retrieving scan {key}: {str(e)}")
            raise KeyError(key)

    def __delitem__(self, key):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM scans WHERE scan_id = ?", (key,))
            conn.commit()

    def __contains__(self, key):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute("SELECT 1 FROM scans WHERE scan_id = ?", (key,))
            return cursor.fetchone() is not None

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute("SELECT scan_id, data FROM scans")
                for scan_id, data_str in cursor.fetchall():
                    try:
                        yield scan_id, json.loads(data_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding scan data for {scan_id}: {str(e)}")
                        continue
        except sqlite3.Error as e:
            logger.error(f"Database error in items(): {str(e)}")
            return

    def __len__(self):
        """Return the number of scans in the database"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM scans")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Database error in __len__: {str(e)}")
            return 0

    def values(self):
        """Return all scan data values"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.execute("SELECT data FROM scans")
                for (data_str,) in cursor.fetchall():
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding scan data: {str(e)}")
                        continue
        except sqlite3.Error as e:
            logger.error(f"Database error in values(): {str(e)}")
            return

# Cleanup function for old uploads
def cleanup_old_uploads(max_age_days: int = 7):
    """
    Delete uploaded codebases older than max_age_days.
    This prevents the uploads folder from growing indefinitely.
    """
    uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
    
    if not os.path.exists(uploads_dir):
        return
    
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    deleted_count = 0
    
    try:
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)
            
            if os.path.isdir(item_path):
                # Get directory creation time
                dir_created = datetime.fromtimestamp(os.path.getctime(item_path))
                
                # Delete if older than cutoff
                if dir_created < cutoff_time:
                    try:
                        shutil.rmtree(item_path)
                        deleted_count += 1
                        logger.info(f"Deleted old upload directory: {item} (created {dir_created})")
                    except Exception as e:
                        logger.error(f"Failed to delete {item}: {str(e)}")
        
        if deleted_count > 0:
            logger.info(f"Cleanup complete: Deleted {deleted_count} old upload(s)")
        else:
            logger.info("Cleanup complete: No old uploads to delete")
            
    except Exception as e:
        logger.error(f"Error during upload cleanup: {str(e)}")

# Run cleanup on startup
cleanup_old_uploads()

scan_results_store = SQLiteScanStore()

@app.get("/")
async def root():
    return {
        "name": "ThreatModelerX",
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
        report_generator = ReportGenerator()
        try:
            report_path = report_generator.generate_report(scan_data, format=export_format)
            
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



@app.post("/api/upload")
async def upload_codebase(file: UploadFile = File(...)):
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Create a unique directory for this upload
    scan_id = uuid.uuid4().hex
    extract_path = os.path.join(upload_dir, scan_id)
    os.makedirs(extract_path, exist_ok=True)
    
    file_path = os.path.join(extract_path, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # If it's a zip file, extract it
        if file.filename.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            # Remove the zip file after extraction
            os.remove(file_path)
            
            # If the zip contained a single top-level directory, use that as the root
            items = os.listdir(extract_path)
            if len(items) == 1 and os.path.isdir(os.path.join(extract_path, items[0])):
                extract_path = os.path.join(extract_path, items[0])
                
        return {"path": extract_path, "message": "File uploaded and extracted successfully"}
        
    except Exception as e:
        logger.error(f"Error handling upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

def cleanup_uploads():
    """Periodically clean up old uploaded files"""
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    if not os.path.exists(upload_dir):
        return
        
    # Retention period: 24 hours
    retention_seconds = 86400
    now = datetime.utcnow().timestamp()
    
    for item in os.listdir(upload_dir):
        item_path = os.path.join(upload_dir, item)
        try:
            # Check modification time
            mtime = os.path.getmtime(item_path)
            if now - mtime > retention_seconds:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
                logger.info(f"Cleaned up old upload: {item}")
        except Exception as e:
            logger.error(f"Error cleaning up {item}: {str(e)}")

@app.on_event("startup")
async def startup_event():
    # Run cleanup on startup
    cleanup_uploads()

@app.post("/api/scan", response_model=dict)
@app.post("/scan", response_model=dict)  # Add additional route to match frontend request
async def create_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    scan_id = f"SCAN-{uuid.uuid4().hex[:12]}"
    
    logger.info(f"Received scan request: {request.dict()}")
    
    project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    
    
    # Check if the provided path exists (for uploaded files or absolute paths)
    if os.path.exists(request.repo_path):
        repo_path = request.repo_path
        logger.info(f"Using provided path: {repo_path}")
    elif "python-flask" in request.repo_path:
        repo_path = os.path.join(project_root, "demo-apps", "python-flask")
    elif "node-express" in request.repo_path:
        repo_path = os.path.join(project_root, "demo-apps", "node-express")
    else:
        # Only default to python-flask if it's one of the known demo paths or empty
        if "demo-apps" in request.repo_path or not request.repo_path:
             repo_path = os.path.join(project_root, "demo-apps", "python-flask")
        else:
             # If a custom path was provided but doesn't exist, we'll fail later
             repo_path = request.repo_path
    
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
    scan_id = f"SCAN-{uuid.uuid4().hex[:12]}"
    
    logger.info(f"Received auto scan request: {request.dict()}")
    
    project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    
    if "python-flask" in request.repo_path:
        repo_path = os.path.join(project_root, "demo-apps", "python-flask")
    elif "node-express" in request.repo_path:
        repo_path = os.path.join(project_root, "demo-apps", "node-express")
    else:
        repo_path = os.path.join(project_root, "demo-apps", "python-flask")
        
    logger.info(f"Using hardcoded demo path for auto scan: {repo_path}")
    
    if not os.path.exists(repo_path):
        logger.error(f"Path does not exist: {repo_path}")
        raise HTTPException(status_code=400, detail=f"Repository path not found: {repo_path}")

    scan_results_store[scan_id] = {
        "status": "running",
        "repo_path": repo_path,
        "started_at": datetime.utcnow().isoformat()
    }

    try:
        result = await run_scan(scan_id, request)
        
        findings = result.get("findings", [])
        threats = result.get("threats", [])
        
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
                    timeout=300.0  # 5 minute timeout for production codebases
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

        if "dast" in request.scan_types or "all" in request.scan_types:
            update_progress("running DAST scanner", "55%", "Initializing ZAP scanner")
            if request.target_url:
                try:
                    zap_runner = ZapRunner()
                    logger.info(f"Starting DAST scan for {request.target_url}")
                    
                    # Run ZAP scan with timeout
                    zap_task = asyncio.create_task(zap_runner.scan(request))
                    zap_findings = await asyncio.wait_for(zap_task, timeout=1800.0) # 30 min timeout for DAST
                    
                    all_findings.extend(zap_findings)
                    update_progress("DAST scan completed", "60%", f"Found {len(zap_findings)} DAST vulnerabilities")
                except asyncio.TimeoutError:
                    logger.warning(f"DAST scan timed out for {scan_id}")
                    all_findings.append(Finding(
                        title="DAST Scan Timeout",
                        description="The DAST scan timed out. Some results may be missing.",
                        severity=SeverityLevel.MEDIUM,
                        tool="OWASP ZAP",
                        file_path="",
                        line_number=0
                    ))
                except Exception as e:
                    logger.error(f"Error running DAST scan: {str(e)}")
                    # Don't fail the whole scan if DAST fails
            else:
                logger.info("Skipping DAST scan: No target URL provided")
                update_progress("skipping DAST", "60%", "No target URL provided for DAST")

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
    try:
        total_scans = 0
        completed_scans = 0
        total_findings = 0
        total_threats = 0
        severity_breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for scan_id, scan_data in scan_results_store.items():
            try:
                total_scans += 1
                if scan_data.get("status") == "completed":
                    completed_scans += 1
                    result = scan_data.get("result", {})
                    summary = result.get("summary", {})
                    
                    total_findings += summary.get("total_findings", 0)
                    total_threats += summary.get("total_threats", 0)

                    by_severity = summary.get("by_severity", {})
                    for severity, count in by_severity.items():
                        severity_key = severity.upper()
                        if severity_key in severity_breakdown:
                            severity_breakdown[severity_key] += count
            except Exception as e:
                logger.error(f"Error processing scan {scan_id} in statistics: {str(e)}")
                continue

        return {
            "total_scans": total_scans,
            "completed_scans": completed_scans,
            "total_findings": total_findings,
            "total_threats": total_threats,
            "severity_breakdown": severity_breakdown
        }
    except Exception as e:
        logger.error(f"Error generating statistics: {str(e)}")
        return {
            "total_scans": 0,
            "completed_scans": 0,
            "total_findings": 0,
            "total_threats": 0,
            "severity_breakdown": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.delete("/api/scan/{scan_id}")
async def delete_scan(scan_id: str):
    """Delete a specific scan from the database"""
    try:
        if scan_id in scan_results_store:
            del scan_results_store[scan_id]
            logger.info(f"Deleted scan: {scan_id}")
            return {"status": "success", "message": f"Scan {scan_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    except Exception as e:
        logger.error(f"Error deleting scan {scan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting scan: {str(e)}")

@app.post("/api/scans/clear")
async def clear_all_scans():
    """Clear all scans from the database (use with caution)"""
    try:
        # Get all scan IDs first
        scan_ids = list(scan_results_store.items())
        count = len(scan_ids)
        
        # Delete all scans
        for scan_id, _ in scan_ids:
            try:
                del scan_results_store[scan_id]
            except Exception as e:
                logger.error(f"Error deleting scan {scan_id}: {str(e)}")
        
        logger.info(f"Cleared {count} scans from database")
        return {"status": "success", "message": f"Cleared {count} scans", "count": count}
    except Exception as e:
        logger.error(f"Error clearing scans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing scans: {str(e)}")

@app.post("/api/uploads/cleanup")
async def cleanup_uploads(max_age_days: int = 7):
    """
    Manually trigger cleanup of old upload directories.
    Deletes uploads older than max_age_days (default: 7 days)
    """
    try:
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        
        if not os.path.exists(uploads_dir):
            return {
                "status": "success",
                "message": "No uploads directory found",
                "deleted_count": 0,
                "space_freed_mb": 0
            }
        
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        space_freed = 0
        
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)
            
            if os.path.isdir(item_path):
                dir_created = datetime.fromtimestamp(os.path.getctime(item_path))
                
                if dir_created < cutoff_time:
                    # Calculate directory size before deletion
                    dir_size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, _, filenames in os.walk(item_path)
                        for filename in filenames
                    )
                    
                    try:
                        shutil.rmtree(item_path)
                        deleted_count += 1
                        space_freed += dir_size
                        logger.info(f"Deleted old upload: {item} (created {dir_created}, size {dir_size} bytes)")
                    except Exception as e:
                        logger.error(f"Failed to delete {item}: {str(e)}")
        
        space_freed_mb = round(space_freed / (1024 * 1024), 2)
        
        return {
            "status": "success",
            "message": f"Cleanup complete: Deleted {deleted_count} upload(s) older than {max_age_days} days",
            "deleted_count": deleted_count,
            "space_freed_mb": space_freed_mb,
            "cutoff_date": cutoff_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error during manual cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")

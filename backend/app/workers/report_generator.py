import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
import jinja2
import pdfkit
from pathlib import Path

logger = logging.getLogger("threatmodelx.workers.report_generator")

class ReportGenerator:
    """
    Generates PDF and HTML reports from scan results
    """
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the report generator
        
        Args:
            templates_dir: Directory containing report templates
        """
        if templates_dir is None:
            # Use default templates directory relative to this file
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
            
        # Create templates directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
            
        self.templates_dir = templates_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Create default templates if they don't exist
        self._ensure_default_templates()
        
    def _ensure_default_templates(self):
        """Create default templates if they don't exist"""
        default_html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ report.title }}</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1, h2, h3 {
                    color: #2c3e50;
                }
                .header {
                    background-color: #34495e;
                    color: white;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                }
                .summary {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                .findings-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }
                .findings-table th, .findings-table td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                .findings-table th {
                    background-color: #f2f2f2;
                }
                .findings-table tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                .severity-critical {
                    background-color: #ffdddd;
                }
                .severity-high {
                    background-color: #ffeecc;
                }
                .severity-medium {
                    background-color: #ffffcc;
                }
                .severity-low {
                    background-color: #e6ffe6;
                }
                .footer {
                    margin-top: 30px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #7f8c8d;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ report.title }}</h1>
                <p>Generated: {{ report.timestamp }}</p>
            </div>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <p>Scan ID: {{ report.scan_id }}</p>
                <p>Repository: {{ report.repo_path }}</p>
                <p>Total Findings: {{ report.total_findings }}</p>
                <ul>
                    <li>Critical: {{ report.critical_count }}</li>
                    <li>High: {{ report.high_count }}</li>
                    <li>Medium: {{ report.medium_count }}</li>
                    <li>Low: {{ report.low_count }}</li>
                </ul>
                <p>Total Threats: {{ report.total_threats }}</p>
            </div>
            
            <h2>Findings</h2>
            <table class="findings-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Severity</th>
                        <th>Description</th>
                        <th>Location</th>
                        <th>CWE</th>
                    </tr>
                </thead>
                <tbody>
                    {% for finding in report.findings %}
                    <tr class="severity-{{ finding.severity|lower }}">
                        <td>{{ finding.id }}</td>
                        <td>{{ finding.severity }}</td>
                        <td>{{ finding.description }}</td>
                        <td>{{ finding.file }}{% if finding.line %}:{{ finding.line }}{% endif %}</td>
                        <td>{% if finding.cwe %}CWE-{{ finding.cwe }}{% endif %}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <h2>Threats</h2>
            <table class="findings-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Description</th>
                        <th>Component</th>
                        <th>Attack Vector</th>
                    </tr>
                </thead>
                <tbody>
                    {% for threat in report.threats %}
                    <tr>
                        <td>{{ threat.category }}</td>
                        <td>{{ threat.description }}</td>
                        <td>{{ threat.component }}</td>
                        <td>{{ threat.attack_vector }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div class="footer">
                <p>Generated by ThreatModelerX v1.0.0</p>
            </div>
        </body>
        </html>
        """
        
        # Write default HTML template if it doesn't exist
        html_template_path = os.path.join(self.templates_dir, "report.html")
        if not os.path.exists(html_template_path):
            with open(html_template_path, "w") as f:
                f.write(default_html_template)
                
    def generate_report(self, scan_result: Dict[str, Any], format: str = "html", output_path: Optional[str] = None) -> str:
        """
        Generate a report from scan results
        
        Args:
            scan_result: The scan result data
            format: Report format ('html' or 'pdf')
            output_path: Path to save the report (optional)
            
        Returns:
            Path to the generated report
        """
        # Prepare report data
        report_data = self._prepare_report_data(scan_result)
        
        # Generate HTML report
        html_content = self._generate_html(report_data)
        
        # Determine output path if not provided
        if output_path is None:
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_id = scan_result.get("scan_id", "unknown")
            
            if format == "html":
                output_path = os.path.join(reports_dir, f"report_{scan_id}_{timestamp}.html")
            else:
                output_path = os.path.join(reports_dir, f"report_{scan_id}_{timestamp}.pdf")
        
        # Save report
        if format == "html":
            with open(output_path, "w") as f:
                f.write(html_content)
            logger.info(f"HTML report saved to {output_path}")
        else:
            try:
                # Convert HTML to PDF
                pdfkit.from_string(html_content, output_path)
                logger.info(f"PDF report saved to {output_path}")
            except Exception as e:
                logger.error(f"Error generating PDF report: {str(e)}")
                # Fallback to HTML if PDF generation fails
                html_path = output_path.replace(".pdf", ".html")
                with open(html_path, "w") as f:
                    f.write(html_content)
                logger.info(f"Fallback HTML report saved to {html_path}")
                output_path = html_path
                
        return output_path
    
    def _prepare_report_data(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for report template"""
        findings = scan_result.get("findings", [])
        threats = scan_result.get("threats", [])
        
        # Count findings by severity
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        
        for finding in findings:
            severity = finding.get("severity", "").upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return {
            "title": f"Security Scan Report - {scan_result.get('scan_id', 'Unknown')}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_id": scan_result.get("scan_id", "Unknown"),
            "repo_path": scan_result.get("repo_path", "Unknown"),
            "findings": findings,
            "threats": threats,
            "total_findings": len(findings),
            "total_threats": len(threats),
            "critical_count": severity_counts["CRITICAL"],
            "high_count": severity_counts["HIGH"],
            "medium_count": severity_counts["MEDIUM"],
            "low_count": severity_counts["LOW"]
        }
    
    def _generate_html(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML report from template"""
        template = self.env.get_template("report.html")
        return template.render(report=report_data)
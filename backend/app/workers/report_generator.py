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
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
        os.makedirs(templates_dir, exist_ok=True)
        self.templates_dir = templates_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        self._ensure_default_templates()
    def _ensure_default_templates(self):
        html_template_path = os.path.join(self.templates_dir, "report.html")
        if not os.path.exists(html_template_path):
            with open(html_template_path, "w") as f:
                f.write(default_html_template)
    def generate_report(self, scan_result: Dict[str, Any], format: str = "html", output_path: Optional[str] = None) -> str:
        report_data = self._prepare_report_data(scan_result)
        html_content = self._generate_html(report_data)
        if output_path is None:
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_id = scan_result.get("scan_id", "unknown")
            if format == "html":
                output_path = os.path.join(reports_dir, f"report_{scan_id}_{timestamp}.html")
            else:
                output_path = os.path.join(reports_dir, f"report_{scan_id}_{timestamp}.pdf")
        if format == "html":
            with open(output_path, "w") as f:
                f.write(html_content)
            logger.info(f"HTML report saved to {output_path}")
        else:
            try:
                pdfkit.from_string(html_content, output_path)
                logger.info(f"PDF report saved to {output_path}")
            except Exception as e:
                logger.error(f"Error generating PDF report: {str(e)}")
                html_path = output_path.replace(".pdf", ".html")
                with open(html_path, "w") as f:
                    f.write(html_content)
                logger.info(f"Fallback HTML report saved to {html_path}")
                output_path = html_path
        return output_path
    def _prepare_report_data(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        findings = scan_result.get("findings", [])
        threats = scan_result.get("threats", [])
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
        template = self.env.get_template("report.html")
        return template.render(report=report_data)
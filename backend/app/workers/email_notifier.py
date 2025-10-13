import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from ..models import Finding, SeverityLevel, ScanRequest

logger = logging.getLogger("autothreatmap.workers.email_notifier")

class EmailNotifier:
    """
    Email notification system for critical security findings
    """
    
    def __init__(self, 
                 smtp_server: Optional[str] = None,
                 smtp_port: Optional[int] = None,
                 smtp_username: Optional[str] = None,
                 smtp_password: Optional[str] = None,
                 sender_email: Optional[str] = None,
                 use_tls: bool = True):
        """
        Initialize the email notifier
        
        Args:
            smtp_server: SMTP server address (defaults to env var SMTP_SERVER)
            smtp_port: SMTP server port (defaults to env var SMTP_PORT or 587)
            smtp_username: SMTP username (defaults to env var SMTP_USERNAME)
            smtp_password: SMTP password (defaults to env var SMTP_PASSWORD)
            sender_email: Sender email address (defaults to env var SENDER_EMAIL)
            use_tls: Whether to use TLS for SMTP connection
        """
        self.smtp_server = smtp_server or os.environ.get("SMTP_SERVER")
        self.smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.environ.get("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD")
        self.sender_email = sender_email or os.environ.get("SENDER_EMAIL")
        self.use_tls = use_tls
        
    async def notify_critical_findings(self, 
                                      scan_request: ScanRequest, 
                                      findings: List[Finding]) -> bool:
        """
        Send email notification for critical findings
        
        Args:
            scan_request: The scan request containing notification email
            findings: List of findings to check for critical issues
            
        Returns:
            True if notification was sent, False otherwise
        """
        if not scan_request.email_notification or not scan_request.notification_email:
            logger.info("Email notification not requested or no email provided")
            return False
            
        # Filter critical and high severity findings
        critical_findings = [f for f in findings if f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        
        if not critical_findings:
            logger.info("No critical findings to notify about")
            return False
            
        try:
            # Create email content
            subject = f"[SECURITY ALERT] Critical findings in scan {scan_request.scan_id}"
            html_content = self._create_email_content(scan_request, critical_findings)
            
            # Send email
            return self._send_email(scan_request.notification_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def _create_email_content(self, scan_request: ScanRequest, findings: List[Finding]) -> str:
        """Create HTML email content for critical findings"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #d9534f; }}
                h2 {{ color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                .finding {{ margin-bottom: 20px; padding: 15px; border-left: 4px solid #d9534f; background-color: #f9f9f9; }}
                .critical {{ border-left-color: #d9534f; }}
                .high {{ border-left-color: #f0ad4e; }}
                .severity {{ font-weight: bold; }}
                .critical-text {{ color: #d9534f; }}
                .high-text {{ color: #f0ad4e; }}
                .details {{ margin-top: 10px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Security Alert: Critical Findings Detected</h1>
                <p>The security scan <strong>{scan_request.scan_id}</strong> has detected {len(findings)} critical or high severity findings that require immediate attention.</p>
                
                <h2>Summary</h2>
                <p>
                    Repository: <strong>{scan_request.repo_path}</strong><br>
                    Scan ID: <strong>{scan_request.scan_id}</strong><br>
                    Critical Findings: <strong>{sum(1 for f in findings if f.severity == SeverityLevel.CRITICAL)}</strong><br>
                    High Severity Findings: <strong>{sum(1 for f in findings if f.severity == SeverityLevel.HIGH)}</strong>
                </p>
                
                <h2>Critical Findings</h2>
        """
        
        # Add each finding
        for finding in findings:
            severity_class = "critical" if finding.severity == SeverityLevel.CRITICAL else "high"
            severity_text_class = "critical-text" if finding.severity == SeverityLevel.CRITICAL else "high-text"
            
            html += f"""
                <div class="finding {severity_class}">
                    <div class="severity {severity_text_class}">{finding.severity.name}</div>
                    <h3>{finding.description}</h3>
                    <div class="details">
                        <p><strong>File:</strong> {finding.file}</p>
                        <p><strong>Line:</strong> {finding.line}</p>
                        <p><strong>Tool:</strong> {finding.tool}</p>
                        <p><strong>CWE:</strong> {finding.cwe or "N/A"}</p>
                        <p><strong>Risk Score:</strong> {finding.risk_score:.1f}</p>
                        <p><strong>Evidence:</strong> <pre>{finding.evidence}</pre></p>
                        <p><strong>Fix Suggestion:</strong> {finding.fix_suggestion}</p>
                    </div>
                </div>
            """
        
        html += """
                <div class="footer">
                    <p>This is an automated security alert from AutoThreatMap. Please address these issues promptly.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_email(self, recipient_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.sender_email]):
            logger.error("SMTP configuration incomplete. Check environment variables.")
            return False
            
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
                
            logger.info(f"Email notification sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
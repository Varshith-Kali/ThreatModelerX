import logging
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from ..models import Finding, SeverityLevel, ScanRequest
logger = logging.getLogger("threatmodelx.workers.email_notifier")
class EmailNotifier:
    def __init__(self, 
                 smtp_server: Optional[str] = None,
                 smtp_port: Optional[int] = None,
                 smtp_username: Optional[str] = None,
                 smtp_password: Optional[str] = None,
                 sender_email: Optional[str] = None,
                 use_tls: bool = True):
        self.smtp_server = smtp_server or os.environ.get("SMTP_SERVER")
        self.smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.environ.get("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD")
        self.sender_email = sender_email or os.environ.get("SENDER_EMAIL")
        self.use_tls = use_tls
    async def notify_critical_findings(self, 
                                      scan_request: ScanRequest, 
                                      findings: List[Finding]) -> bool:
        if not scan_request.email_notification or not scan_request.notification_email:
            logger.info("Email notification not requested or no email provided")
            return False
        critical_findings = [f for f in findings if f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        if not critical_findings:
            logger.info("No critical findings to notify about")
            return False
        try:
            subject = f"[SECURITY ALERT] Critical findings in scan {scan_request.scan_id}"
            html_content = self._create_email_content(scan_request, critical_findings)
            return self._send_email(scan_request.notification_email, subject, html_content)
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    def _create_email_content(self, scan_request: ScanRequest, findings: List[Finding]) -> str:
        for finding in findings:
            severity_class = "critical" if finding.severity == SeverityLevel.CRITICAL else "high"
            severity_text_class = "critical-text" if finding.severity == SeverityLevel.CRITICAL else "high-text"
        return html
    def _send_email(self, recipient_email: str, subject: str, html_content: str) -> bool:
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.sender_email]):
            logger.error("SMTP configuration incomplete. Check environment variables.")
            return False
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient_email
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
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
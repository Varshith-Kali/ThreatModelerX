from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
class FindingStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    FIXED = "FIXED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
class Finding(BaseModel):
    id: str
    tool: str
    language: Optional[str] = None
    file: str
    line: Optional[int] = None
    cwe: Optional[str] = None
    severity: SeverityLevel
    description: str
    evidence: Optional[str] = None
    fix_suggestion: Optional[str] = None
    risk_score: Optional[float] = None
    component: Optional[str] = None
    status: FindingStatus = FindingStatus.OPEN
    manual_review: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reviewer_comments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
class ThreatCategory(str, Enum):
    SPOOFING = "SPOOFING"
    TAMPERING = "TAMPERING"
    REPUDIATION = "REPUDIATION"
    INFORMATION_DISCLOSURE = "INFORMATION_DISCLOSURE"
    DENIAL_OF_SERVICE = "DENIAL_OF_SERVICE"
    ELEVATION_OF_PRIVILEGE = "ELEVATION_OF_PRIVILEGE"
class Threat(BaseModel):
    id: str
    category: ThreatCategory
    description: str
    component: str
    attack_vector: str
    mitre_ids: List[str] = []
    cwe_ids: List[str] = []
    risk_level: SeverityLevel
    manual_review: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reviewer_comments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    mitigation: str
class ScanRequest(BaseModel):
    repo_path: str
    scan_types: List[str] = ["sast", "dast", "threat_model"]
    target_url: Optional[HttpUrl] = None
    include_dast: bool = False
    email_notification: bool = False
    notification_email: Optional[str] = None
    export_format: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
class ScanResult(BaseModel):
    scan_id: str
    repo_path: str
    timestamp: datetime
    findings: List[Finding]
    threats: List[Threat]
    summary: Dict[str, Any]
    risk_score: float
class RemediationPlan(BaseModel):
    finding_id: str
    priority: int
    estimated_effort: str
    steps: List[str]
    code_snippet: Optional[str] = None
    resources: List[str] = []

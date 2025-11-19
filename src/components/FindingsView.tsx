import { useState, useEffect } from 'react';
import { AlertCircle, ChevronDown, ChevronRight, ExternalLink, CheckCircle, Shield, AlertTriangle, AlertOctagon, Download, Filter, X } from 'lucide-react';
import ManualReview from './ManualReview';

interface FindingsViewProps {
  scanId: string | null;
}

interface Finding {
  id: string;
  tool: string;
  language: string;
  file: string;
  line: number;
  cwe: string;
  severity: string;
  description: string;
  evidence: string;
  fix_suggestion: string;
  risk_score: number;
  status: string;
  manual_review?: any;
  reviewer_comments?: any[];
}

interface RemediationPlan {
  finding_id: string;
  priority: number;
  estimated_effort: string;
  steps: string[];
  code_snippet: string;
  resources: string[];
}

function FindingsView({ scanId }: FindingsViewProps) {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFinding, setSelectedFinding] = useState<string | null>(null);
  const [remediationPlan, setRemediationPlan] = useState<RemediationPlan | null>(null);
  const [expandedFindings, setExpandedFindings] = useState<Set<string>>(new Set());
  const [filterSeverity, setFilterSeverity] = useState<string>('all');

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    fetchFindings();
  }, [scanId, filterSeverity]);

  const downloadReport = () => {
    if (!scanId) return;
    window.open(`${API_BASE}/api/report/${scanId}?format=html`, '_blank');
  };

  const fetchFindings = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/api/findings`;
      if (scanId) {
        url += `?scan_id=${scanId}`;
      }
      if (filterSeverity !== 'all') {
        url += `${scanId ? '&' : '?'}severity=${filterSeverity}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      setFindings(data.findings);
    } catch (error) {
      console.error('Error fetching findings:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRemediationPlan = async (findingId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/remediation/${findingId}`);
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      const data = await response.json();
      setRemediationPlan(data);
      setSelectedFinding(findingId);
    } catch (error) {
      console.error('Error fetching remediation plan:', error);
    }
  };

  const handleReviewSubmit = async (findingId: string, reviewData: any) => {
    try {
      const response = await fetch(`${API_BASE}/api/findings/${findingId}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reviewData),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();

      // Update the finding in the local state
      setFindings(findings.map(finding =>
        finding.id === findingId
          ? { ...finding, status: reviewData.status, manual_review: reviewData, reviewer_comments: [...(finding.reviewer_comments || []), { comment: reviewData.comment, reviewer: reviewData.reviewer, timestamp: new Date().toISOString() }] }
          : finding
      ));

      return data;
    } catch (error) {
      console.error('Error submitting review:', error);
      throw error;
    }
  };

  const toggleExpanded = (findingId: string) => {
    const newExpanded = new Set(expandedFindings);
    if (newExpanded.has(findingId)) {
      newExpanded.delete(findingId);
    } else {
      newExpanded.add(findingId);
    }
    setExpandedFindings(newExpanded);
  };

  const getSeverityColor = (severity: string) => {
    const colors = {
      CRITICAL: 'bg-critical/10 text-critical border-critical/30',
      HIGH: 'bg-high/10 text-high border-high/30',
      MEDIUM: 'bg-medium/10 text-medium border-medium/30',
      LOW: 'bg-low/10 text-low border-low/30',
      INFO: 'bg-accent-DEFAULT/10 text-accent-DEFAULT border-accent-DEFAULT/30'
    };
    return colors[severity as keyof typeof colors] || 'bg-secondary-light text-accent-DEFAULT border-highlight';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <AlertOctagon className="h-4 w-4 mr-1.5" />;
      case 'HIGH':
        return <AlertTriangle className="h-4 w-4 mr-1.5" />;
      case 'MEDIUM':
        return <AlertCircle className="h-4 w-4 mr-1.5" />;
      case 'LOW':
        return <Shield className="h-4 w-4 mr-1.5" />;
      default:
        return <AlertCircle className="h-4 w-4 mr-1.5" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-DEFAULT"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-text-primary tracking-tight">Security Findings</h1>
        <div className="flex items-center space-x-4">
          <button
            onClick={downloadReport}
            disabled={!scanId}
            className="btn-primary px-4 py-2 rounded-lg flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4" />
            <span>Download Report</span>
          </button>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-muted" />
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="pl-10 pr-4 py-2 bg-secondary border border-highlight rounded-lg text-text-primary focus:outline-none focus:border-accent-DEFAULT transition-colors appearance-none cursor-pointer"
            >
              <option value="all">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-text-primary flex items-center">
            <Shield className="mr-2 h-5 w-5 text-accent-DEFAULT" />
            {findings.length} Finding{findings.length !== 1 ? 's' : ''} Detected
          </h2>
        </div>

        {findings.length === 0 ? (
          <div className="text-center py-16 bg-primary-light/30 rounded-lg border border-dashed border-highlight">
            <CheckCircle className="h-16 w-16 text-low mx-auto mb-4 animate-pulse" />
            <p className="text-text-primary text-lg font-medium">No security issues found!</p>
            <p className="text-text-secondary mt-2">The scan completed successfully with no findings matching your criteria.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {findings.map((finding, index) => (
              <div
                key={finding.id}
                className={`bg-secondary/50 rounded-lg border border-highlight overflow-hidden hover:border-accent-DEFAULT/50 transition-all duration-300 ${expandedFindings.has(finding.id) ? 'ring-1 ring-accent-DEFAULT/50' : ''}`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div
                  className="p-4 cursor-pointer hover:bg-secondary-light/50 transition-colors"
                  onClick={() => toggleExpanded(finding.id)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center flex-wrap gap-2 mb-2">
                        {expandedFindings.has(finding.id) ? (
                          <ChevronDown className="h-5 w-5 text-accent-DEFAULT" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-text-muted" />
                        )}
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center uppercase tracking-wider ${getSeverityColor(finding.severity)}`}>
                          {getSeverityIcon(finding.severity)}
                          {finding.severity}
                        </span>
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-light text-text-secondary border border-highlight">
                          {finding.tool}
                        </span>
                        {finding.risk_score && (
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-accent-DEFAULT/10 text-accent-DEFAULT border border-accent-DEFAULT/20">
                            Risk: {finding.risk_score}
                          </span>
                        )}
                      </div>
                      <h3 className="text-text-primary font-medium mb-1 text-lg">{finding.description}</h3>
                      <p className="text-text-muted text-sm font-mono">
                        {finding.file}:{finding.line} {finding.cwe && <span className="ml-2 px-1.5 py-0.5 rounded bg-primary-light text-xs text-text-secondary">{finding.cwe}</span>}
                      </p>
                    </div>
                    <div className={`p-2 rounded-full ${finding.severity === 'CRITICAL' ? 'bg-critical/10 text-critical' :
                        finding.severity === 'HIGH' ? 'bg-high/10 text-high' :
                          finding.severity === 'MEDIUM' ? 'bg-medium/10 text-medium' :
                            'bg-low/10 text-low'
                      }`}>
                      <AlertCircle className="h-6 w-6" />
                    </div>
                  </div>
                </div>

                {expandedFindings.has(finding.id) && (
                  <div className="border-t border-highlight bg-primary-light/20 p-6 space-y-6 animate-fade-in">
                    {finding.evidence && (
                      <div>
                        <h4 className="text-accent-DEFAULT font-medium mb-2 text-sm uppercase tracking-wider">Evidence</h4>
                        <pre className="bg-primary-light p-4 rounded-lg text-sm text-text-secondary overflow-x-auto font-mono border border-highlight">
                          {finding.evidence}
                        </pre>
                      </div>
                    )}

                    {finding.fix_suggestion && (
                      <div>
                        <h4 className="text-accent-DEFAULT font-medium mb-2 text-sm uppercase tracking-wider">Fix Suggestion</h4>
                        <div className="bg-primary-light/50 p-4 rounded-lg border border-highlight">
                          <p className="text-text-primary">{finding.fix_suggestion}</p>
                        </div>
                      </div>
                    )}

                    <div className="flex flex-wrap gap-4 pt-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          fetchRemediationPlan(finding.id);
                        }}
                        className="btn-primary px-4 py-2 rounded-lg flex items-center space-x-2 text-sm"
                      >
                        <ExternalLink className="h-4 w-4" />
                        <span>Generate Remediation Plan</span>
                      </button>
                    </div>

                    <div className="mt-6 pt-6 border-t border-highlight">
                      <ManualReview
                        findingId={finding.id}
                        initialStatus={finding.status}
                        onReviewSubmit={(reviewData) => handleReviewSubmit(finding.id, reviewData)}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {remediationPlan && selectedFinding && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-secondary rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-highlight shadow-2xl">
            <div className="sticky top-0 bg-secondary/95 backdrop-blur border-b border-highlight p-6 z-10">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-text-primary flex items-center">
                  <Shield className="mr-3 h-6 w-6 text-accent-DEFAULT" />
                  Remediation Plan
                </h2>
                <button
                  onClick={() => {
                    setRemediationPlan(null);
                    setSelectedFinding(null);
                  }}
                  className="p-2 hover:bg-primary-light rounded-full text-text-muted hover:text-text-primary transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="flex items-center space-x-3 mt-4">
                <span className="px-3 py-1 rounded-full bg-accent-DEFAULT/10 text-accent-DEFAULT text-sm font-medium border border-accent-DEFAULT/20">
                  Priority: {remediationPlan.priority}
                </span>
                <span className="px-3 py-1 rounded-full bg-primary-light text-text-secondary text-sm font-medium border border-highlight">
                  Effort: {remediationPlan.estimated_effort}
                </span>
              </div>
            </div>

            <div className="p-6 space-y-8">
              <div>
                <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center">
                  <span className="flex items-center justify-center w-6 h-6 rounded-full bg-accent-DEFAULT text-primary text-xs font-bold mr-2">1</span>
                  Remediation Steps
                </h3>
                <ol className="space-y-4 ml-3 border-l-2 border-highlight pl-6 relative">
                  {remediationPlan.steps.map((step, index) => (
                    <li key={index} className="relative">
                      <span className="absolute -left-[31px] top-0 w-4 h-4 rounded-full bg-highlight border-2 border-secondary"></span>
                      <span className="text-text-secondary leading-relaxed">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {remediationPlan.code_snippet && (
                <div>
                  <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-accent-DEFAULT text-primary text-xs font-bold mr-2">2</span>
                    Code Example
                  </h3>
                  <div className="relative group">
                    <pre className="bg-primary-light p-4 rounded-lg text-sm text-text-secondary overflow-x-auto font-mono border border-highlight group-hover:border-accent-DEFAULT/30 transition-colors">
                      {remediationPlan.code_snippet}
                    </pre>
                  </div>
                </div>
              )}

              {remediationPlan.resources && remediationPlan.resources.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-accent-DEFAULT text-primary text-xs font-bold mr-2">3</span>
                    Additional Resources
                  </h3>
                  <ul className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {remediationPlan.resources.map((resource, index) => (
                      <li key={index}>
                        <a
                          href={resource}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center p-3 rounded-lg bg-primary-light hover:bg-primary-light/80 border border-highlight hover:border-accent-DEFAULT/50 transition-all group"
                        >
                          <ExternalLink className="h-4 w-4 text-accent-DEFAULT mr-3 group-hover:scale-110 transition-transform" />
                          <span className="text-text-secondary group-hover:text-text-primary truncate text-sm">{resource}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default FindingsView;

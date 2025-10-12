import { useState, useEffect } from 'react';
import { AlertCircle, ChevronDown, ChevronRight, ExternalLink, CheckCircle, Shield, AlertTriangle, AlertOctagon } from 'lucide-react';
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
      CRITICAL: 'bg-red-700 text-white border-red-600',
      HIGH: 'bg-red-600 text-white border-red-500',
      MEDIUM: 'bg-orange-500 text-white border-orange-400',
      LOW: 'bg-blue-500 text-white border-blue-400',
      INFO: 'bg-gray-500 text-white border-gray-400'
    };
    return colors[severity as keyof typeof colors] || 'bg-secondary-light text-accent border-highlight';
  };
  
  const getSeverityIcon = (severity: string) => {
    switch(severity) {
      case 'CRITICAL':
        return <AlertOctagon className="h-4 w-4 mr-1" />;
      case 'HIGH':
        return <AlertTriangle className="h-4 w-4 mr-1" />;
      case 'MEDIUM':
        return <AlertCircle className="h-4 w-4 mr-1" />;
      case 'LOW':
        return <Shield className="h-4 w-4 mr-1" />;
      default:
        return <AlertCircle className="h-4 w-4 mr-1" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-highlight"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-accent">Security Findings</h1>
        <div className="flex items-center space-x-4">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-secondary border border-highlight rounded-lg px-4 py-2 text-accent focus:outline-none focus:ring-2 focus:ring-highlight"
          >
            <option value="all">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      <div className="bg-secondary-dark rounded-xl p-6 border border-secondary shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">
            {findings.length} Finding{findings.length !== 1 ? 's' : ''} Detected
          </h2>
        </div>

        {findings.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-400 mx-auto mb-4" />
            <p className="text-slate-300 text-lg">No security issues found!</p>
            <p className="text-slate-400 mt-2">The scan completed successfully with no findings.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {findings.map((finding) => (
              <div
                key={finding.id}
                className="bg-secondary/80 rounded-lg border border-secondary overflow-hidden shadow-md"
              >
                <div
                  className="p-4 cursor-pointer hover:bg-secondary transition-colors"
                  onClick={() => toggleExpanded(finding.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {expandedFindings.has(finding.id) ? (
                          <ChevronDown className="h-5 w-5 text-accent" />
                        ) : (
                          <ChevronRight className="h-5 w-5 text-accent" />
                        )}
                        <span className={`px-2 py-1 rounded text-xs font-medium border flex items-center ${getSeverityColor(finding.severity)}`}>
                          {getSeverityIcon(finding.severity)}
                          {finding.severity}
                        </span>
                        <span className="px-2 py-1 rounded text-xs bg-secondary text-accent">
                          {finding.tool}
                        </span>
                        {finding.risk_score && (
                           <span className="px-2 py-1 rounded text-xs bg-highlight/20 text-accent">
                             Risk: {finding.risk_score}
                           </span>
                          )}
                      </div>
                      <h3 className="text-white font-medium mb-1">{finding.description}</h3>
                      <p className="text-slate-400 text-sm">
                        {finding.file}:{finding.line} {finding.cwe && `• ${finding.cwe}`}
                      </p>
                    </div>
                    <AlertCircle className="h-6 w-6 text-orange-400 flex-shrink-0 ml-4" />
                  </div>
                </div>

                {expandedFindings.has(finding.id) && (
                  <div className="border-t border-secondary p-4 space-y-4">
                    {finding.evidence && (
                      <div>
                        <h4 className="text-accent font-medium mb-2">Evidence:</h4>
                        <pre className="bg-secondary-dark p-3 rounded text-sm text-accent overflow-x-auto shadow-inner">
                          {finding.evidence}
                        </pre>
                      </div>
                    )}

                    {finding.fix_suggestion && (
                      <div>
                        <h4 className="text-accent font-medium mb-2">Fix Suggestion:</h4>
                        <p className="text-accent/80">{finding.fix_suggestion}</p>
                      </div>
                    )}

                    <button
                      onClick={() => fetchRemediationPlan(finding.id)}
                      className="px-4 py-2 bg-highlight text-accent rounded-lg hover:bg-primary-light transition-colors flex items-center space-x-2 shadow-md"
                    >
                      <ExternalLink className="h-4 w-4" />
                      <span>View Remediation Plan</span>
                    </button>
                    
                    <div className="mt-4">
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
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-slate-700">
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 p-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">Remediation Plan</h2>
                <button
                  onClick={() => {
                    setRemediationPlan(null);
                    setSelectedFinding(null);
                  }}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>
              <div className="flex items-center space-x-3 mt-2">
                <span className="px-3 py-1 rounded bg-cyan-500/20 text-cyan-400 text-sm">
                  Priority: {remediationPlan.priority}
                </span>
                <span className="px-3 py-1 rounded bg-highlight/20 text-highlight text-sm">
                  Effort: {remediationPlan.estimated_effort}
                </span>
              </div>
            </div>

            <div className="p-6 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white mb-3">Remediation Steps</h3>
                <ol className="space-y-2">
                  {remediationPlan.steps.map((step, index) => (
                    <li key={index} className="flex items-start space-x-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm">
                        {index + 1}
                      </span>
                      <span className="text-slate-300">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {remediationPlan.code_snippet && (
                <div>
                  <h3 className="text-lg font-bold text-white mb-3">Code Example</h3>
                  <pre className="bg-slate-900 p-4 rounded text-sm text-slate-300 overflow-x-auto">
                    {remediationPlan.code_snippet}
                  </pre>
                </div>
              )}

              {remediationPlan.resources && remediationPlan.resources.length > 0 && (
                <div>
                  <h3 className="text-lg font-bold text-white mb-3">Additional Resources</h3>
                  <ul className="space-y-2">
                    {remediationPlan.resources.map((resource, index) => (
                      <li key={index}>
                        <a
                          href={resource}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-cyan-400 hover:text-cyan-300 flex items-center space-x-2"
                        >
                          <ExternalLink className="h-4 w-4" />
                          <span>{resource}</span>
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

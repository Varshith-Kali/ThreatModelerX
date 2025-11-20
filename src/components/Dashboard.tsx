import { useState, useEffect } from 'react';
import { Activity, AlertCircle, Shield, TrendingUp, RefreshCw } from 'lucide-react';

interface DashboardProps {
  onViewScan: (scanId: string) => void;
}

interface Stats {
  total_scans: number;
  completed_scans: number;
  total_findings: number;
  total_threats: number;
  severity_breakdown: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
}

interface Scan {
  scan_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
}

function Dashboard({ onViewScan }: DashboardProps) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, scansRes] = await Promise.all([
        fetch(`${API_BASE}/api/stats`),
        fetch(`${API_BASE}/api/scans`)
      ]);

      const statsData = await statsRes.json();
      const scansData = await scansRes.json();

      setStats(statsData);
      setScans(scansData.scans);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-DEFAULT"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-text-primary tracking-tight">Security Dashboard</h1>
        <button
          onClick={fetchData}
          className="btn-primary px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
        <div className="card p-6 delay-100 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm uppercase tracking-wider">Total Scans</p>
              <p className="text-4xl font-bold text-accent-DEFAULT mt-2">{stats?.total_scans || 0}</p>
            </div>
            <div className="p-3 bg-primary-light rounded-full">
              <Activity className="h-8 w-8 text-accent-DEFAULT" />
            </div>
          </div>
        </div>

        <div className="card p-6 delay-200 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm uppercase tracking-wider">Total Findings</p>
              <p className="text-4xl font-bold text-critical mt-2">{stats?.total_findings || 0}</p>
            </div>
            <div className="p-3 bg-primary-light rounded-full">
              <AlertCircle className="h-8 w-8 text-critical" />
            </div>
          </div>
        </div>

        <div className="card p-6 delay-300 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm uppercase tracking-wider">Threats Detected</p>
              <p className="text-4xl font-bold text-high mt-2">{stats?.total_threats || 0}</p>
            </div>
            <div className="p-3 bg-primary-light rounded-full">
              <Shield className="h-8 w-8 text-high" />
            </div>
          </div>
        </div>

        <div className="card p-6 delay-300 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm uppercase tracking-wider">Critical Issues</p>
              <p className="text-4xl font-bold text-critical mt-2">
                {stats?.severity_breakdown.CRITICAL || 0}
              </p>
            </div>
            <div className="p-3 bg-primary-light rounded-full">
              <TrendingUp className="h-8 w-8 text-critical" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card p-6">
          <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center">
            <AlertCircle className="mr-2 h-5 w-5 text-accent-DEFAULT" />
            Severity Breakdown
          </h2>
          <div className="space-y-4">
            {stats && Object.entries(stats.severity_breakdown).map(([severity, count]) => {
              const colors = {
                CRITICAL: 'bg-critical shadow-[0_0_10px_rgba(255,82,82,0.5)]',
                HIGH: 'bg-high shadow-[0_0_10px_rgba(255,171,64,0.5)]',
                MEDIUM: 'bg-medium shadow-[0_0_10px_rgba(255,215,64,0.5)]',
                LOW: 'bg-low shadow-[0_0_10px_rgba(105,240,174,0.5)]'
              };

              const total = stats.total_findings || 1;
              const percentage = ((count / total) * 100).toFixed(1);

              return (
                <div key={severity} className="group">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-text-secondary font-medium group-hover:text-text-primary transition-colors">{severity}</span>
                    <span className="text-text-muted group-hover:text-accent-DEFAULT transition-colors">{count} ({percentage}%)</span>
                  </div>
                  <div className="w-full bg-primary-light rounded-full h-2 overflow-hidden">
                    <div
                      className={`${colors[severity as keyof typeof colors]} h-2 rounded-full transition-all duration-1000 ease-out`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center">
            <Activity className="mr-2 h-5 w-5 text-accent-DEFAULT" />
            Recent Scans
          </h2>
          <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
            {scans.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-text-muted">No scans yet.</p>
                <p className="text-text-secondary text-sm mt-2">Start a new scan to see results here.</p>
              </div>
            ) : (
              scans.slice(0, 10).map((scan) => (
                <div
                  key={scan.scan_id}
                  className="flex items-center justify-between p-4 bg-primary-light/50 rounded-lg hover:bg-primary-light border border-transparent hover:border-accent-DEFAULT/30 transition-all cursor-pointer group"
                  onClick={() => scan.status === 'completed' && onViewScan(scan.scan_id)}
                >
                  <div>
                    <p className="text-text-primary font-medium group-hover:text-accent-DEFAULT transition-colors">{scan.scan_id}</p>
                    <p className="text-text-muted text-xs mt-1">
                      {new Date(scan.started_at).toLocaleString()}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${scan.status === 'completed'
                      ? 'bg-low/10 text-low border border-low/20'
                      : scan.status === 'running'
                        ? 'bg-accent-DEFAULT/10 text-accent-DEFAULT border border-accent-DEFAULT/20 animate-pulse'
                        : 'bg-critical/10 text-critical border border-critical/20'
                      }`}
                  >
                    {scan.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

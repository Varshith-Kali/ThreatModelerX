import { useState, useEffect } from 'react';
import { Activity, AlertCircle, Shield, TrendingUp } from 'lucide-react';

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-accent">Dashboard</h1>
        <button
          onClick={fetchData}
          className="px-4 py-2 rounded-lg bg-highlight text-accent border border-accent hover:bg-secondary-light transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full">
        <div className="bg-secondary rounded-xl p-6 border border-highlight shadow-lg hover:shadow-xl transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Total Scans</p>
              <p className="text-3xl font-bold text-accent mt-2">{stats?.total_scans || 0}</p>
            </div>
            <Activity className="h-12 w-12 text-accent" />
          </div>
        </div>

        <div className="bg-secondary rounded-xl p-6 border border-highlight shadow-lg hover:shadow-xl transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Total Findings</p>
              <p className="text-3xl font-bold text-accent mt-2">{stats?.total_findings || 0}</p>
            </div>
            <AlertCircle className="h-12 w-12 text-accent" />
          </div>
        </div>

        <div className="bg-secondary rounded-xl p-6 border border-highlight shadow-lg hover:shadow-xl transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Threats Detected</p>
              <p className="text-3xl font-bold text-accent mt-2">{stats?.total_threats || 0}</p>
            </div>
            <Shield className="h-12 w-12 text-accent" />
          </div>
        </div>

        <div className="bg-secondary rounded-xl p-6 border border-highlight shadow-lg hover:shadow-xl transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-text-secondary text-sm">Critical Findings</p>
              <p className="text-3xl font-bold text-accent mt-2">
                {stats?.severity_breakdown.CRITICAL || 0}
              </p>
            </div>
            <TrendingUp className="h-12 w-12 text-accent" />
          </div>
        </div>
      </div>

      <div className="bg-secondary rounded-xl p-6 border border-highlight">
        <h2 className="text-xl font-bold text-accent mb-4">Severity Breakdown</h2>
        <div className="space-y-3">
          {stats && Object.entries(stats.severity_breakdown).map(([severity, count]) => {
            const colors = {
              CRITICAL: 'bg-red-500',
              HIGH: 'bg-orange-500',
              MEDIUM: 'bg-yellow-500',
              LOW: 'bg-highlight'
            };

            const total = stats.total_findings || 1;
            const percentage = ((count / total) * 100).toFixed(1);

            return (
              <div key={severity}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-accent">{severity}</span>
                  <span className="text-accent/70">{count} ({percentage}%)</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className={`${colors[severity as keyof typeof colors]} h-2 rounded-full transition-all`}
                    style={{ width: `${percentage}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-secondary rounded-xl p-6 border border-highlight">
        <h2 className="text-xl font-bold text-accent mb-4">Recent Scans</h2>
        <div className="space-y-3">
          {scans.length === 0 ? (
            <p className="text-accent/70 text-center py-4">No scans yet. Start a new scan to begin.</p>
          ) : (
            scans.slice(0, 10).map((scan) => (
              <div
                key={scan.scan_id}
                className="flex items-center justify-between p-4 bg-secondary/80 rounded-lg hover:bg-secondary-light transition-colors cursor-pointer"
                onClick={() => scan.status === 'completed' && onViewScan(scan.scan_id)}
              >
                <div>
                  <p className="text-accent font-medium">{scan.scan_id}</p>
                  <p className="text-accent/70 text-sm">
                    {new Date(scan.started_at).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-sm ${
                    scan.status === 'completed'
                      ? 'bg-green-500/20 text-green-400'
                      : scan.status === 'running'
                      ? 'bg-highlight/20 text-highlight'
                      : 'bg-red-500/20 text-red-400'
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
  );
}

export default Dashboard;

import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Target, UserX, FileWarning, Clock, FileX, Zap, UserPlus } from 'lucide-react';

interface ThreatViewProps {
  scanId: string | null;
}

interface Threat {
  id: string;
  category: string;
  description: string;
  component: string;
  attack_vector: string;
  mitre_ids: string[];
  cwe_ids: string[];
  risk_level: string;
  mitigation: string;
}

function ThreatView({ scanId }: ThreatViewProps) {
  const [threats, setThreats] = useState<Threat[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    fetchThreats();
  }, [scanId]);

  const fetchThreats = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/api/threats`;
      if (scanId) {
        url += `?scan_id=${scanId}`;
      }

      const response = await fetch(url);
      const data = await response.json();
      setThreats(data.threats);
    } catch (error) {
      console.error('Error fetching threats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      SPOOFING: 'bg-purple-700 text-white border-purple-600',
      TAMPERING: 'bg-red-700 text-white border-red-600',
      REPUDIATION: 'bg-yellow-600 text-white border-yellow-500',
      INFORMATION_DISCLOSURE: 'bg-blue-700 text-white border-blue-600',
      DENIAL_OF_SERVICE: 'bg-orange-600 text-white border-orange-500',
      ELEVATION_OF_PRIVILEGE: 'bg-red-600 text-white border-red-500'
    };
    return colors[category] || 'bg-primary-light/20 text-accent border-highlight';
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      CRITICAL: 'bg-red-700 text-white',
      HIGH: 'bg-red-600 text-white',
      MEDIUM: 'bg-orange-500 text-white',
      LOW: 'bg-blue-500 text-white'
    };
    return colors[severity] || 'bg-secondary-light text-accent';
  };

  const filteredThreats = selectedCategory === 'all'
    ? threats
    : threats.filter(t => t.category === selectedCategory);

  const categories = Array.from(new Set(threats.map(t => t.category)));
  const categoryStats = categories.map(cat => ({
    category: cat,
    count: threats.filter(t => t.category === cat).length
  }));

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
        <h1 className="text-3xl font-bold text-accent">Security Threats</h1>
        <div className="flex items-center space-x-4">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-secondary border border-highlight rounded-lg px-4 py-2 text-accent focus:outline-none focus:ring-2 focus:ring-highlight focus:border-highlight shadow-md"
          >
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {categoryStats.map(({ category, count }) => (
          <div
            key={category}
            className={`p-4 rounded-lg border ${getCategoryColor(category)} cursor-pointer hover:opacity-80 transition-opacity shadow-lg hover:shadow-xl transition-all`}
            onClick={() => setSelectedCategory(category)}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">{category.replace(/_/g, ' ')}</p>
                <p className="text-sm opacity-75">{count} threat{count !== 1 ? 's' : ''}</p>
              </div>
              {category === 'SPOOFING' && <UserX className="h-8 w-8 opacity-80" />}
              {category === 'TAMPERING' && <FileWarning className="h-8 w-8 opacity-80" />}
              {category === 'REPUDIATION' && <Clock className="h-8 w-8 opacity-80" />}
              {category === 'INFORMATION_DISCLOSURE' && <FileX className="h-8 w-8 opacity-80" />}
              {category === 'DENIAL_OF_SERVICE' && <Zap className="h-8 w-8 opacity-80" />}
              {category === 'ELEVATION_OF_PRIVILEGE' && <UserPlus className="h-8 w-8 opacity-80" />}
              {!['SPOOFING', 'TAMPERING', 'REPUDIATION', 'INFORMATION_DISCLOSURE', 'DENIAL_OF_SERVICE', 'ELEVATION_OF_PRIVILEGE'].includes(category) && 
                <Shield className="h-8 w-8 opacity-80" />
              }
            </div>
          </div>
        ))}
      </div>

      <div className="bg-secondary-dark rounded-xl p-6 border border-secondary shadow-lg">
        <h2 className="text-xl font-bold text-accent mb-4">
          {filteredThreats.length} Threat{filteredThreats.length !== 1 ? 's' : ''} Identified
        </h2>

        {filteredThreats.length === 0 ? (
          <div className="text-center py-12 shadow-lg">
            <Shield className="h-16 w-16 text-highlight mx-auto mb-4" />
            <p className="text-accent text-lg">No threats found in this category</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredThreats.map((threat) => (
              <div
                key={threat.id}
                className="bg-secondary/80 rounded-lg border border-secondary p-4 shadow-md hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <span className={`px-3 py-1 rounded text-sm font-medium border ${getCategoryColor(threat.category)}`}>
                      {threat.category.replace(/_/g, ' ')}
                    </span>
                    <span className={`px-3 py-1 rounded text-sm text-accent ${getSeverityColor(threat.risk_level)}`}>
                      {threat.risk_level}
                    </span>
                  </div>
                  {threat.category === 'SPOOFING' && <UserX className="h-6 w-6 text-purple-500 flex-shrink-0" />}
                  {threat.category === 'TAMPERING' && <FileWarning className="h-6 w-6 text-red-500 flex-shrink-0" />}
                  {threat.category === 'REPUDIATION' && <Clock className="h-6 w-6 text-yellow-500 flex-shrink-0" />}
                  {threat.category === 'INFORMATION_DISCLOSURE' && <FileX className="h-6 w-6 text-blue-500 flex-shrink-0" />}
                  {threat.category === 'DENIAL_OF_SERVICE' && <Zap className="h-6 w-6 text-orange-500 flex-shrink-0" />}
                  {threat.category === 'ELEVATION_OF_PRIVILEGE' && <UserPlus className="h-6 w-6 text-red-500 flex-shrink-0" />}
                  {!['SPOOFING', 'TAMPERING', 'REPUDIATION', 'INFORMATION_DISCLOSURE', 'DENIAL_OF_SERVICE', 'ELEVATION_OF_PRIVILEGE'].includes(threat.category) && 
                    <AlertTriangle className="h-6 w-6 text-highlight flex-shrink-0" />
                  }
                </div>

                <h3 className="text-accent font-medium text-lg mb-2">{threat.description}</h3>

                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-accent/70">Component:</span>
                    <span className="text-accent ml-2">{threat.component}</span>
                  </div>

                  <div>
                    <span className="text-accent/70">Attack Vector:</span>
                    <p className="text-accent mt-1">{threat.attack_vector}</p>
                  </div>

                  {threat.mitre_ids && threat.mitre_ids.length > 0 && (
                    <div>
                      <span className="text-accent/70">MITRE ATT&CK:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {threat.mitre_ids.map((id) => (
                          <a
                            key={id}
                            href={`https://attack.mitre.org/techniques/${id}/`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-2 py-1 bg-secondary text-accent rounded hover:bg-primary-light transition-colors shadow-sm"
                          >
                            {id}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {threat.cwe_ids && threat.cwe_ids.length > 0 && (
                    <div>
                      <span className="text-accent/70">CWE:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {threat.cwe_ids.map((cwe) => (
                          <a
                            key={cwe}
                            href={`https://cwe.mitre.org/data/definitions/${cwe.replace('CWE-', '')}.html`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-2 py-1 bg-secondary text-accent rounded hover:bg-primary-light transition-colors shadow-sm"
                          >
                            {cwe}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-slate-600">
                    <span className="text-slate-400 font-medium">Mitigation:</span>
                    <p className="text-slate-300 mt-1">{threat.mitigation}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="bg-secondary-dark rounded-xl p-6 border border-secondary shadow-lg">
        <h2 className="text-xl font-bold text-accent mb-4">STRIDE Framework</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="p-4 bg-secondary/80 rounded-lg shadow-md hover:shadow-lg transition-all">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-5 w-5 text-highlight" />
              <h3 className="font-medium text-accent">Spoofing</h3>
            </div>
            <p className="text-accent/70">Impersonating users or systems</p>
          </div>
          <div className="p-4 bg-secondary/80 rounded-lg shadow-md hover:shadow-lg transition-all">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-5 w-5 text-highlight" />
              <h3 className="font-medium text-accent">Tampering</h3>
            </div>
            <p className="text-accent/70">Modifying data or code</p>
          </div>
          <div className="p-4 bg-secondary/80 rounded-lg shadow-md hover:shadow-lg transition-all">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-5 w-5 text-highlight" />
              <h3 className="font-medium text-accent">Repudiation</h3>
            </div>
            <p className="text-accent/70">Denying actions or transactions</p>
          </div>
          <div className="p-4 bg-secondary/80 rounded-lg shadow-md hover:shadow-lg transition-all">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-5 w-5 text-highlight" />
              <h3 className="font-medium text-accent">Information Disclosure</h3>
            </div>
            <p className="text-accent/70">Exposing sensitive data</p>
          </div>
          <div className="p-4 bg-secondary/80 rounded-lg shadow-md hover:shadow-lg transition-all">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-5 w-5 text-highlight" />
              <h3 className="font-medium text-accent">Denial of Service</h3>
            </div>
            <p className="text-accent/70">Disrupting system availability</p>
          </div>
          <div className="p-4 bg-secondary/80 rounded-lg shadow-md hover:shadow-lg transition-all">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="h-5 w-5 text-highlight" />
              <h3 className="font-medium text-accent">Elevation of Privilege</h3>
            </div>
            <p className="text-accent/70">Gaining unauthorized access</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ThreatView;

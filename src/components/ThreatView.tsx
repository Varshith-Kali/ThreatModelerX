import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, Target, UserX, FileWarning, Clock, FileX, Zap, UserPlus, Filter } from 'lucide-react';

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
      SPOOFING: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
      TAMPERING: 'bg-red-500/10 text-red-400 border-red-500/30',
      REPUDIATION: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      INFORMATION_DISCLOSURE: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
      DENIAL_OF_SERVICE: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
      ELEVATION_OF_PRIVILEGE: 'bg-pink-500/10 text-pink-400 border-pink-500/30'
    };
    return colors[category] || 'bg-primary-light text-accent-DEFAULT border-highlight';
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      CRITICAL: 'bg-critical/10 text-critical border border-critical/30',
      HIGH: 'bg-high/10 text-high border border-high/30',
      MEDIUM: 'bg-medium/10 text-medium border border-medium/30',
      LOW: 'bg-low/10 text-low border border-low/30'
    };
    return colors[severity] || 'bg-secondary-light text-accent-DEFAULT';
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-DEFAULT"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-text-primary tracking-tight">Security Threats</h1>
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-muted" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="pl-10 pr-4 py-2 bg-secondary border border-highlight rounded-lg text-text-primary focus:outline-none focus:border-accent-DEFAULT transition-colors appearance-none cursor-pointer shadow-md"
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>{cat.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {categoryStats.map(({ category, count }, index) => (
          <div
            key={category}
            className={`p-4 rounded-lg border ${getCategoryColor(category)} cursor-pointer hover:opacity-80 transition-all shadow-lg hover:shadow-xl hover:-translate-y-1`}
            onClick={() => setSelectedCategory(category)}
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="font-bold text-lg">{category.replace(/_/g, ' ')}</p>
                <p className="text-sm opacity-75 mt-1">{count} threat{count !== 1 ? 's' : ''}</p>
              </div>
              <div className="p-2 rounded-full bg-black/20">
                {category === 'SPOOFING' && <UserX className="h-6 w-6" />}
                {category === 'TAMPERING' && <FileWarning className="h-6 w-6" />}
                {category === 'REPUDIATION' && <Clock className="h-6 w-6" />}
                {category === 'INFORMATION_DISCLOSURE' && <FileX className="h-6 w-6" />}
                {category === 'DENIAL_OF_SERVICE' && <Zap className="h-6 w-6" />}
                {category === 'ELEVATION_OF_PRIVILEGE' && <UserPlus className="h-6 w-6" />}
                {!['SPOOFING', 'TAMPERING', 'REPUDIATION', 'INFORMATION_DISCLOSURE', 'DENIAL_OF_SERVICE', 'ELEVATION_OF_PRIVILEGE'].includes(category) &&
                  <Shield className="h-6 w-6" />
                }
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-6">
        <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center">
          <Shield className="mr-2 h-5 w-5 text-accent-DEFAULT" />
          {filteredThreats.length} Threat{filteredThreats.length !== 1 ? 's' : ''} Identified
        </h2>

        {filteredThreats.length === 0 ? (
          <div className="text-center py-16 bg-primary-light/30 rounded-lg border border-dashed border-highlight">
            <Shield className="h-16 w-16 text-low mx-auto mb-4 animate-pulse" />
            <p className="text-text-primary text-lg font-medium">No threats found in this category</p>
            <p className="text-text-secondary mt-2">Your system appears secure against these specific threats.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredThreats.map((threat, index) => (
              <div
                key={threat.id}
                className="bg-secondary/50 rounded-lg border border-highlight p-6 shadow-md hover:shadow-lg hover:border-accent-DEFAULT/50 transition-all duration-300 group"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center flex-wrap gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-wider ${getCategoryColor(threat.category)}`}>
                      {threat.category.replace(/_/g, ' ')}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getSeverityColor(threat.risk_level)}`}>
                      {threat.risk_level}
                    </span>
                  </div>
                  <div className="p-2 rounded-full bg-primary-light group-hover:bg-accent-DEFAULT/10 transition-colors">
                    {threat.category === 'SPOOFING' && <UserX className="h-5 w-5 text-purple-400" />}
                    {threat.category === 'TAMPERING' && <FileWarning className="h-5 w-5 text-red-400" />}
                    {threat.category === 'REPUDIATION' && <Clock className="h-5 w-5 text-yellow-400" />}
                    {threat.category === 'INFORMATION_DISCLOSURE' && <FileX className="h-5 w-5 text-blue-400" />}
                    {threat.category === 'DENIAL_OF_SERVICE' && <Zap className="h-5 w-5 text-orange-400" />}
                    {threat.category === 'ELEVATION_OF_PRIVILEGE' && <UserPlus className="h-5 w-5 text-pink-400" />}
                    {!['SPOOFING', 'TAMPERING', 'REPUDIATION', 'INFORMATION_DISCLOSURE', 'DENIAL_OF_SERVICE', 'ELEVATION_OF_PRIVILEGE'].includes(threat.category) &&
                      <AlertTriangle className="h-5 w-5 text-text-muted" />
                    }
                  </div>
                </div>

                <h3 className="text-text-primary font-bold text-lg mb-3 group-hover:text-accent-DEFAULT transition-colors">{threat.description}</h3>

                <div className="space-y-4 text-sm">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-primary-light/50 p-3 rounded-lg border border-highlight">
                      <span className="text-text-muted text-xs uppercase tracking-wider block mb-1">Component</span>
                      <span className="text-text-primary font-mono">{threat.component}</span>
                    </div>

                    <div className="bg-primary-light/50 p-3 rounded-lg border border-highlight">
                      <span className="text-text-muted text-xs uppercase tracking-wider block mb-1">Attack Vector</span>
                      <p className="text-text-primary">{threat.attack_vector}</p>
                    </div>
                  </div>

                  {threat.mitre_ids && threat.mitre_ids.length > 0 && (
                    <div>
                      <span className="text-text-muted text-xs uppercase tracking-wider block mb-2">MITRE ATT&CK</span>
                      <div className="flex flex-wrap gap-2">
                        {threat.mitre_ids.map((id) => (
                          <a
                            key={id}
                            href={`https://attack.mitre.org/techniques/${id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-2 py-1 bg-primary-light text-accent-DEFAULT rounded hover:bg-accent-DEFAULT/20 transition-colors text-xs font-mono border border-highlight hover:border-accent-DEFAULT/50"
                          >
                            {id}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {threat.cwe_ids && threat.cwe_ids.length > 0 && (
                    <div>
                      <span className="text-text-muted text-xs uppercase tracking-wider block mb-2">CWE</span>
                      <div className="flex flex-wrap gap-2">
                        {threat.cwe_ids.map((cwe) => (
                          <a
                            key={cwe}
                            href={`https://cwe.mitre.org/data/definitions/${cwe.replace('CWE-', '')}.html`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-2 py-1 bg-primary-light text-text-secondary rounded hover:bg-primary-light/80 transition-colors text-xs font-mono border border-highlight"
                          >
                            {cwe}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t border-highlight mt-4">
                    <span className="text-accent-DEFAULT font-medium flex items-center mb-2">
                      <Shield className="h-4 w-4 mr-2" />
                      Mitigation Strategy
                    </span>
                    <p className="text-text-secondary leading-relaxed bg-primary-light/30 p-3 rounded-lg border border-highlight/50">{threat.mitigation}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card p-6">
        <h2 className="text-xl font-bold text-text-primary mb-6 flex items-center">
          <Target className="mr-2 h-5 w-5 text-accent-DEFAULT" />
          STRIDE Framework Reference
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
          <div className="p-4 bg-primary-light/50 rounded-lg border border-highlight hover:border-accent-DEFAULT/30 hover:bg-primary-light transition-all group">
            <div className="flex items-center space-x-2 mb-2">
              <UserX className="h-5 w-5 text-purple-400 group-hover:scale-110 transition-transform" />
              <h3 className="font-bold text-text-primary group-hover:text-accent-DEFAULT transition-colors">Spoofing</h3>
            </div>
            <p className="text-text-secondary text-xs leading-relaxed">Impersonating users or systems to gain unauthorized access.</p>
          </div>
          <div className="p-4 bg-primary-light/50 rounded-lg border border-highlight hover:border-accent-DEFAULT/30 hover:bg-primary-light transition-all group">
            <div className="flex items-center space-x-2 mb-2">
              <FileWarning className="h-5 w-5 text-red-400 group-hover:scale-110 transition-transform" />
              <h3 className="font-bold text-text-primary group-hover:text-accent-DEFAULT transition-colors">Tampering</h3>
            </div>
            <p className="text-text-secondary text-xs leading-relaxed">Modifying data or code to compromise integrity.</p>
          </div>
          <div className="p-4 bg-primary-light/50 rounded-lg border border-highlight hover:border-accent-DEFAULT/30 hover:bg-primary-light transition-all group">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="h-5 w-5 text-yellow-400 group-hover:scale-110 transition-transform" />
              <h3 className="font-bold text-text-primary group-hover:text-accent-DEFAULT transition-colors">Repudiation</h3>
            </div>
            <p className="text-text-secondary text-xs leading-relaxed">Denying actions or transactions to avoid accountability.</p>
          </div>
          <div className="p-4 bg-primary-light/50 rounded-lg border border-highlight hover:border-accent-DEFAULT/30 hover:bg-primary-light transition-all group">
            <div className="flex items-center space-x-2 mb-2">
              <FileX className="h-5 w-5 text-blue-400 group-hover:scale-110 transition-transform" />
              <h3 className="font-bold text-text-primary group-hover:text-accent-DEFAULT transition-colors">Information Disclosure</h3>
            </div>
            <p className="text-text-secondary text-xs leading-relaxed">Exposing sensitive data to unauthorized parties.</p>
          </div>
          <div className="p-4 bg-primary-light/50 rounded-lg border border-highlight hover:border-accent-DEFAULT/30 hover:bg-primary-light transition-all group">
            <div className="flex items-center space-x-2 mb-2">
              <Zap className="h-5 w-5 text-orange-400 group-hover:scale-110 transition-transform" />
              <h3 className="font-bold text-text-primary group-hover:text-accent-DEFAULT transition-colors">Denial of Service</h3>
            </div>
            <p className="text-text-secondary text-xs leading-relaxed">Disrupting system availability to legitimate users.</p>
          </div>
          <div className="p-4 bg-primary-light/50 rounded-lg border border-highlight hover:border-accent-DEFAULT/30 hover:bg-primary-light transition-all group">
            <div className="flex items-center space-x-2 mb-2">
              <UserPlus className="h-5 w-5 text-pink-400 group-hover:scale-110 transition-transform" />
              <h3 className="font-bold text-text-primary group-hover:text-accent-DEFAULT transition-colors">Elevation of Privilege</h3>
            </div>
            <p className="text-text-secondary text-xs leading-relaxed">Gaining unauthorized access or higher privileges.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ThreatView;

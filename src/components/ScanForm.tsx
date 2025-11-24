import { useState } from 'react';
import { PlayCircle, Loader2, Shield, Code, Terminal, FileCode, Server, Coffee, Zap, Upload, FolderOpen } from 'lucide-react';
import ScanProgress from './ScanProgress';
import ScanLogs from './ScanLogs';

interface ScanFormProps {
  onScanComplete: (scanId: string) => void;
}

function ScanForm({ onScanComplete }: ScanFormProps) {
  const [repoPath, setRepoPath] = useState('./demo-apps/python-flask');
  const [scanSource, setScanSource] = useState<'demo' | 'custom' | 'upload'>('demo');
  const [uploading, setUploading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [scanTypes, setScanTypes] = useState(['sast', 'threat_model']);
  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);

  const [showLogs, setShowLogs] = useState(false);

  const API_BASE = 'http://localhost:8000';

  const demoApps = [
    { value: './demo-apps/python-flask', label: 'Python Flask', icon: <Coffee className="h-5 w-5 text-yellow-400" />, description: 'Vulnerable Python web application' },
    { value: './demo-apps/node-express', label: 'Node.js Express', icon: <Server className="h-5 w-5 text-green-400" />, description: 'Vulnerable Node.js API service' },
    { value: './demo-apps/java-spring', label: 'Java Spring', icon: <Coffee className="h-5 w-5 text-red-400" />, description: 'Vulnerable Java enterprise app' },
    { value: './demo-apps/go-gin', label: 'Go Gin', icon: <Zap className="h-5 w-5 text-blue-400" />, description: 'Vulnerable Go microservice' },
  ];

  const availableScanTypes = [
    { value: 'sast', label: 'Static Analysis (SAST)', icon: <Code className="h-5 w-5 text-accent-DEFAULT" />, description: 'Semgrep, Bandit, Retire.js' },
    { value: 'threat_modeling', label: 'Threat Modeling', icon: <Shield className="h-5 w-5 text-accent-DEFAULT" />, description: 'STRIDE + MITRE ATT&CK mapping' },
  ];

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadedFileName(file.name);
      setUploading(true);
      setStatus('Uploading codebase...');

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch(`${API_BASE}/api/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          setRepoPath(data.path);
          setStatus('File uploaded successfully. Ready to scan.');
        } else {
          setStatus('Upload failed. Please try again.');
          setUploadedFileName(null);
        }
      } catch (error) {
        console.error('Upload error:', error);
        setStatus('Upload error. Please check server connection.');
        setUploadedFileName(null);
      } finally {
        setUploading(false);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setScanning(true);
    setProgress(0);
    setStatus('Initiating scan...');
    setScanId(null);

    try {
      console.log("Starting scan with path:", repoPath);
      let finalPath = repoPath;

      const response = await fetch(`${API_BASE}/api/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: finalPath,
          scan_types: scanTypes
        })
      });

      if (!response.ok) {
        console.error(`Server error: ${response.status}`);
        setStatus(`Error: Server responded with status ${response.status}`);
        setScanning(false);
        return;
      }

      const data = await response.json();
      console.log("Scan response:", data);

      if (!data.scan_id) {
        setStatus("Error: Invalid response from server");
        setScanning(false);
        return;
      }

      setScanId(data.scan_id);
      setStatus('Scan running...');
      setProgress(5);

      pollScanStatus(data.scan_id);
    } catch (error: any) {
      console.error("Scan error:", error);
      setStatus(`Error starting scan: ${error.message || 'Unknown error'}`);
      setScanning(false);
    }
  };

  const pollScanStatus = async (id: string) => {
    let retryCount = 0;
    const maxRetries = 300; // 10 minutes timeout
    const retryDelay = 2000;

    const interval = setInterval(async () => {
      try {
        console.log(`Polling scan status for ${id}, attempt ${retryCount + 1}`);
        const response = await fetch(`${API_BASE}/api/scan/${id}`);

        if (!response.ok) {
          console.error(`Scan status check failed: HTTP ${response.status}`);
          retryCount++;
          if (retryCount > maxRetries) {
            clearInterval(interval);
            setStatus(`Scan status unavailable. Please try again.`);
            setScanning(false);
          }
          return;
        }

        retryCount = 0;
        const data = await response.json();

        if (data.status === 'error' || data.status === 'not_found') {
          console.log(`Scan error: ${data.error || 'Unknown error'}`);
          setStatus(`Scan ${data.status}: ${data.error || 'Unknown error'}`);
          setScanning(false);
          clearInterval(interval);
          return;
        }

        if (data.status === 'completed') {
          clearInterval(interval);
          setStatus('Scan completed!');
          setScanning(false);
          setProgress(100);
          setTimeout(() => {
            onScanComplete(id);
          }, 1500);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setStatus(`Scan failed: ${data.error || 'Unknown error'}`);
          setScanning(false);
        } else if (data.status === 'running') {
          const stage = data.current_stage || 'processing';
          const progressText = data.progress || '';
          const details = data.details || '';

          setStatus(`${stage}${details ? ': ' + details : ''}`);

          if (progressText) {
            const progressValue = parseInt(progressText.replace('%', '')) || 0;
            setProgress(progressValue);
          } else {
            setProgress(prev => Math.min(prev + 2, 95));
          }
        } else {
          setStatus(`Scanning... (${data.status})`);
          setProgress(prev => Math.min(prev + 2, 90));
        }
      } catch (error: any) {
        console.error("Error polling scan status:", error);
        retryCount++;
        if (retryCount > maxRetries) {
          clearInterval(interval);
          setStatus(`Error checking scan status: ${error.message || 'Unknown error'}`);
          setScanning(false);
        }
      }
    }, retryDelay);

    return () => clearInterval(interval);
  };

  const toggleScanType = (type: string) => {
    if (scanTypes.includes(type)) {
      setScanTypes(scanTypes.filter(t => t !== type));
    } else {
      setScanTypes([...scanTypes, type]);
    }
  };

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <div className="card p-8">
        <div className="flex items-center mb-8">
          <div className="p-3 rounded-full bg-accent-DEFAULT/10 mr-4">
            <PlayCircle className="h-8 w-8 text-accent-DEFAULT" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-text-primary tracking-tight">New ThreatModelerX Scan</h1>
            <p className="text-text-secondary mt-1">Configure and launch a comprehensive security analysis</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          <div>
            <label className="block text-text-primary font-bold mb-4 flex items-center text-lg">
              <Terminal className="mr-2 h-5 w-5 text-accent-DEFAULT" />
              Target Repository / Application
            </label>
            <div className="flex space-x-4 mb-6">
              <button
                type="button"
                onClick={() => setScanSource('demo')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${scanSource === 'demo'
                  ? 'bg-accent-DEFAULT text-primary shadow-lg'
                  : 'bg-primary-light border border-highlight text-text-primary hover:bg-secondary-light hover:border-accent-DEFAULT/50'
                  }`}
              >
                <div className="flex items-center justify-center">
                  <Coffee className="w-4 h-4 mr-2" />
                  Demo Apps
                </div>
              </button>
              <button
                type="button"
                onClick={() => setScanSource('upload')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${scanSource === 'upload'
                  ? 'bg-accent-DEFAULT text-primary shadow-lg'
                  : 'bg-primary-light border border-highlight text-text-primary hover:bg-secondary-light hover:border-accent-DEFAULT/50'
                  }`}
              >
                <div className="flex items-center justify-center">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Code
                </div>
              </button>
              <button
                type="button"
                onClick={() => setScanSource('custom')}
                className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${scanSource === 'custom'
                  ? 'bg-accent-DEFAULT text-primary shadow-lg'
                  : 'bg-primary-light border border-highlight text-text-primary hover:bg-secondary-light hover:border-accent-DEFAULT/50'
                  }`}
              >
                <div className="flex items-center justify-center">
                  <FolderOpen className="w-4 h-4 mr-2" />
                  Custom Path
                </div>
              </button>
            </div>

            {scanSource === 'demo' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
                {demoApps.map((app) => (
                  <div
                    key={app.value}
                    onClick={() => !scanning && setRepoPath(app.value)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all duration-300 ${repoPath === app.value
                      ? 'bg-accent-DEFAULT/10 border-accent-DEFAULT ring-1 ring-accent-DEFAULT'
                      : 'bg-secondary border-highlight hover:border-accent-DEFAULT/50 hover:bg-secondary-light'
                      } ${scanning ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="flex items-center mb-2">
                      <div className={`p-2 rounded-full mr-3 ${repoPath === app.value ? 'bg-accent-DEFAULT text-primary' : 'bg-primary-light'}`}>
                        {app.icon}
                      </div>
                      <span className={`font-bold ${repoPath === app.value ? 'text-accent-DEFAULT' : 'text-text-primary'}`}>
                        {app.label}
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary ml-12">{app.description}</p>
                  </div>
                ))}
              </div>
            )}

            {scanSource === 'upload' && (
              <div className="animate-fade-in p-8 border-2 border-dashed border-highlight rounded-lg bg-secondary/50 text-center hover:border-accent-DEFAULT/50 transition-colors relative">
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  accept=".zip,.rar,.7z,application/zip,application/x-zip-compressed"
                  disabled={scanning || uploading}
                />
                <div className="flex flex-col items-center justify-center">
                  {uploading ? (
                    <Loader2 className="h-12 w-12 text-accent-DEFAULT animate-spin mb-4" />
                  ) : (
                    <Upload className="h-12 w-12 text-text-muted mb-4" />
                  )}
                  <h3 className="text-lg font-bold text-text-primary mb-2">
                    {uploading ? 'Uploading...' : uploadedFileName ? 'File Uploaded' : 'Drop your codebase here'}
                  </h3>
                  <p className="text-text-secondary mb-4">
                    {uploadedFileName
                      ? `Ready to scan: ${uploadedFileName}`
                      : 'Support for .zip archives containing your source code'}
                  </p>
                  {!uploadedFileName && (
                    <span className="px-4 py-2 bg-primary-light rounded-md text-sm text-accent-DEFAULT font-mono border border-accent-DEFAULT/20">
                      Click to browse
                    </span>
                  )}
                </div>
              </div>
            )}

            {scanSource === 'custom' && (
              <div className="mt-4 relative animate-fade-in">
                <input
                  type="text"
                  value={repoPath}
                  onChange={(e) => setRepoPath(e.target.value)}
                  className="w-full bg-primary-light border border-highlight rounded-lg pl-10 pr-4 py-3 text-text-primary focus:outline-none focus:border-accent-DEFAULT transition-colors font-mono text-sm"
                  placeholder="Enter absolute path to local directory..."
                  disabled={scanning}
                />
                <FileCode className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-text-muted" />
              </div>
            )}
          </div>

          <div>
            <label className="block text-text-primary font-bold mb-4 flex items-center text-lg">
              <Shield className="mr-2 h-5 w-5 text-accent-DEFAULT" />
              Scan Configuration
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableScanTypes.map((type) => (
                <label
                  key={type.value}
                  className={`flex items-start p-4 rounded-lg border cursor-pointer transition-all duration-300 ${scanTypes.includes(type.value)
                    ? 'bg-accent-DEFAULT/10 border-accent-DEFAULT'
                    : 'bg-secondary border-highlight hover:border-accent-DEFAULT/50 hover:bg-secondary-light'
                    } ${scanning ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center h-5 mt-1">
                    <input
                      type="checkbox"
                      checked={scanTypes.includes(type.value)}
                      onChange={() => toggleScanType(type.value)}
                      disabled={scanning}
                      className="w-4 h-4 text-accent-DEFAULT bg-primary border-highlight rounded focus:ring-accent-DEFAULT focus:ring-offset-0"
                    />
                  </div>
                  <div className="ml-3">
                    <div className="flex items-center mb-1">
                      {type.icon}
                      <span className={`ml-2 font-bold ${scanTypes.includes(type.value) ? 'text-accent-DEFAULT' : 'text-text-primary'}`}>
                        {type.label}
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary">{type.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={scanning || scanTypes.length === 0}
            className="btn-primary w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center space-x-3 shadow-lg hover:shadow-accent-DEFAULT/20 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transform active:scale-[0.99] transition-all"
          >
            {scanning ? (
              <>
                <Loader2 className="h-6 w-6 animate-spin" />
                <span>Running ThreatModelerX Scan...</span>
              </>
            ) : (
              <>
                <PlayCircle className="h-6 w-6" />
                <span>Start Analysis</span>
              </>
            )}
          </button>
        </form>

        {(scanning || status) && (
          <div className="mt-8 animate-fade-in">
            <ScanProgress
              status={status || 'Initiating scan...'}
              progress={progress}
              stage={status}
              error={status.includes('Error') || status.includes('failed') ? status : undefined}
            />
            <div className="flex justify-between text-xs text-text-muted mt-2 font-mono">
              <span>{status}</span>
              <span>{progress}%</span>
            </div>
          </div>
        )}

        {scanId && (
          <div className="mt-6 p-4 bg-primary-light/50 rounded-lg border border-highlight flex justify-between items-center animate-fade-in">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-secondary rounded-md border border-highlight">
                <Terminal className="h-4 w-4 text-accent-DEFAULT" />
              </div>
              <div>
                <p className="text-text-muted text-xs uppercase tracking-wider">Scan ID</p>
                <p className="text-text-primary font-mono text-sm">{scanId}</p>
              </div>
            </div>
            <button
              onClick={() => setShowLogs(!showLogs)}
              className="px-4 py-2 bg-secondary hover:bg-secondary-light text-text-primary text-sm rounded-lg transition-colors border border-highlight hover:border-accent-DEFAULT/50"
            >
              {showLogs ? 'Hide Logs' : 'Show Logs'}
            </button>
          </div>
        )}

        {scanId && <ScanLogs scanId={scanId} visible={showLogs} />}
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center">
            <Code className="mr-2 h-5 w-5 text-accent-DEFAULT" />
            SAST Capabilities
          </h3>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-DEFAULT mt-2 mr-2 flex-shrink-0"></span>
              <span className="text-text-secondary text-sm"><strong>Semgrep:</strong> Multi-language static analysis for finding bugs and enforcing code standards.</span>
            </li>
            <li className="flex items-start">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-DEFAULT mt-2 mr-2 flex-shrink-0"></span>
              <span className="text-text-secondary text-sm"><strong>Bandit:</strong> Security linter designed to find common security issues in Python code.</span>
            </li>
            <li className="flex items-start">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-DEFAULT mt-2 mr-2 flex-shrink-0"></span>
              <span className="text-text-secondary text-sm"><strong>Retire.js:</strong> Scanner for detecting known vulnerabilities in JavaScript libraries.</span>
            </li>
          </ul>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-bold text-text-primary mb-4 flex items-center">
            <Shield className="mr-2 h-5 w-5 text-accent-DEFAULT" />
            Threat Modeling
          </h3>
          <ul className="space-y-3">
            <li className="flex items-start">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-DEFAULT mt-2 mr-2 flex-shrink-0"></span>
              <span className="text-text-secondary text-sm"><strong>STRIDE:</strong> Automated threat generation based on data flow and component interaction.</span>
            </li>
            <li className="flex items-start">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-DEFAULT mt-2 mr-2 flex-shrink-0"></span>
              <span className="text-text-secondary text-sm"><strong>MITRE ATT&CK:</strong> Mapping of identified threats to real-world adversary tactics and techniques.</span>
            </li>
            <li className="flex items-start">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-DEFAULT mt-2 mr-2 flex-shrink-0"></span>
              <span className="text-text-secondary text-sm"><strong>CWE Integration:</strong> Linking vulnerabilities to Common Weakness Enumeration definitions.</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default ScanForm;

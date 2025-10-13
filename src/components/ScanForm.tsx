import { useState } from 'react';
import { PlayCircle, Loader2 } from 'lucide-react';
import ScanProgress from './ScanProgress';
import ScanLogs from './ScanLogs';

interface ScanFormProps {
  onScanComplete: (scanId: string) => void;
}

function ScanForm({ onScanComplete }: ScanFormProps) {
  const [repoPath, setRepoPath] = useState('./demo-apps/python-flask');
  const [scanTypes, setScanTypes] = useState(['sast', 'threat_model']);
  const [scanning, setScanning] = useState(false);
  const [scanId, setScanId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);

  const [showLogs, setShowLogs] = useState(false);

  const API_BASE = 'http://localhost:8000';

  const demoApps = [
    { value: './demo-apps/python-flask', label: 'Python Flask (Vulnerable Demo)' },
    { value: './demo-apps/node-express', label: 'Node.js Express (Vulnerable Demo)' },
    { value: './demo-apps/java-spring', label: 'Java Spring (Vulnerable Demo)' },
    { value: './demo-apps/go-gin', label: 'Go Gin (Vulnerable Demo)' },
  ];

  const availableScanTypes = [
    { value: 'sast', label: 'Static Analysis (SAST)', description: 'Semgrep, Bandit, Retire.js' },
    { value: 'threat_modeling', label: 'Threat Modeling', description: 'STRIDE + MITRE ATT&CK mapping' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setScanning(true);
    setProgress(0);
    setStatus('Initiating scan...');
    setScanId(null); // Reset scan ID when starting a new scan

    try {
      console.log("Starting scan with path:", repoPath);
      // Just use the path as is - backend will handle resolution
      let finalPath = repoPath;

      // Use the /api/scan endpoint
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
      setProgress(5); // Show initial progress

      pollScanStatus(data.scan_id);
    } catch (error: any) {
      console.error("Scan error:", error);
      setStatus(`Error starting scan: ${error.message || 'Unknown error'}`);
      setScanning(false);
    }
  };

  const pollScanStatus = async (id: string) => {
    let retryCount = 0;
    const maxRetries = 30; // Increased retries for longer scans
    const retryDelay = 2000; // 2 seconds between polls
    
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
        
        retryCount = 0; // Reset retry count on successful response
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
          // Display detailed progress information
          const stage = data.current_stage || 'processing';
          const progressText = data.progress || '';
          const details = data.details || '';
          
          // Set status with more detailed information
          setStatus(`${stage}${details ? ': ' + details : ''}`);
          
          // Update progress bar
          if (progressText) {
            const progressValue = parseInt(progressText.replace('%', '')) || 0;
            setProgress(progressValue);
          } else {
            // If no explicit progress, increment slightly to show activity
            setProgress(prev => Math.min(prev + 2, 95)); // Slightly faster progress increment
          }
        } else {
          setStatus(`Scanning... (${data.status})`);
          // Show some progress even when status is indeterminate
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
    
    // Return cleanup function
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
    <div className="max-w-3xl mx-auto">
      <div className="bg-secondary rounded-xl p-8 border border-highlight shadow-lg">
        <h1 className="text-3xl font-bold text-accent mb-6">New Security Scan</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-text-secondary font-medium mb-2">
              Target Repository / Application
            </label>
            <select
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              className="w-full bg-primary border border-highlight rounded-lg px-4 py-3 text-accent focus:outline-none focus:ring-2 focus:ring-highlight"
              disabled={scanning}
            >
              {demoApps.map((app) => (
                <option key={app.value} value={app.value}>
                  {app.label}
                </option>
              ))}
            </select>
            <p className="text-text-secondary text-sm mt-2">
              Select a demo application to scan or provide a custom path
            </p>
          </div>

          <div>
            <label className="block text-text-secondary font-medium mb-3">
              Scan Types
            </label>
            <div className="space-y-3">
              {availableScanTypes.map((type) => (
                <label
                  key={type.value}
                  className={`flex items-start p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    scanTypes.includes(type.value)
                      ? 'bg-highlight/10 border-highlight'
                      : 'bg-primary/50 border-highlight hover:border-highlight'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={scanTypes.includes(type.value)}
                    onChange={() => toggleScanType(type.value)}
                    disabled={scanning}
                    className="mt-1 mr-3 text-highlight focus:ring-highlight"
                  />
                  <div>
                    <div className="text-accent font-medium">{type.label}</div>
                    <div className="text-text-secondary text-sm">{type.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={scanning || scanTypes.length === 0}
            className="w-full bg-highlight text-accent px-6 py-3 rounded-lg font-medium hover:bg-primary-light transition-colors disabled:bg-secondary-light disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {scanning ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>Scanning...</span>
              </>
            ) : (
              <>
                <PlayCircle className="h-5 w-5" />
                <span>Start Scan</span>
              </>
            )}
          </button>
        </form>

        {(scanning || status) && (
          <div className="mt-6">
            <ScanProgress 
              status={status || 'Initiating scan...'}
              progress={progress}
              stage={status}
              error={status.includes('Error') || status.includes('failed') ? status : undefined}
            />
            <div className="text-right text-xs text-accent/70 mt-1">{progress}%</div>
          </div>
        )}

        {scanId && (
          <div className="mt-4 p-4 bg-secondary rounded-lg shadow-md">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-accent/70 text-sm">Scan ID:</p>
                <p className="text-accent font-mono">{scanId}</p>
              </div>
              <button 
                onClick={() => setShowLogs(!showLogs)}
                className="px-3 py-1 bg-primary/50 hover:bg-primary-light text-accent text-sm rounded-md transition-colors"
              >
                {showLogs ? 'Hide Logs' : 'Show Logs'}
              </button>
            </div>
          </div>
        )}
        
        {scanId && <ScanLogs scanId={scanId} visible={showLogs} />}
      </div>

      <div className="mt-8 bg-secondary-dark rounded-xl p-6 border border-secondary shadow-lg">
        <h2 className="text-xl font-bold text-accent mb-4">What Gets Scanned?</h2>
        <ul className="space-y-2 text-accent">
          <li className="flex items-start">
            <span className="text-highlight mr-2">•</span>
            <span><strong>SAST:</strong> Static code analysis using Semgrep (multi-language), Bandit (Python), and Retire.js (JavaScript dependencies)</span>
          </li>
          <li className="flex items-start">
            <span className="text-highlight mr-2">•</span>
            <span><strong>Threat Modeling:</strong> STRIDE-based analysis mapping vulnerabilities to MITRE ATT&CK techniques and CWE categories</span>
          </li>
        </ul>
      </div>
    </div>
  );
}

export default ScanForm;

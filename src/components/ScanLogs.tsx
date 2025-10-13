import { useState, useEffect } from 'react';
import { Terminal, Clock, AlertCircle, CheckCircle } from 'lucide-react';

interface ScanLogsProps {
  scanId: string | null;
  visible: boolean;
}

interface LogEntry {
  timestamp: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
}

function ScanLogs({ scanId, visible }: ScanLogsProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    if (!scanId || !visible) return;
    
    setIsLoading(true);
    
    // Initial log entry
    setLogs([
      {
        timestamp: new Date().toISOString(),
        message: `Starting scan ${scanId}`,
        type: 'info'
      }
    ]);
    
    // Poll for scan status to generate log entries
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/api/scan/${scanId}`);
        
        if (!response.ok) {
          addLog(`Failed to fetch scan status: HTTP ${response.status}`, 'error');
          return;
        }
        
        const data = await response.json();
        
        if (data.status === 'completed') {
          addLog(`Scan completed successfully`, 'success');
          clearInterval(interval);
          setIsLoading(false);
        } else if (data.status === 'failed') {
          addLog(`Scan failed: ${data.error || 'Unknown error'}`, 'error');
          clearInterval(interval);
          setIsLoading(false);
        } else if (data.status === 'running') {
          const stage = data.current_stage || 'processing';
          const details = data.details || '';
          
          if (details) {
            addLog(`${stage}: ${details}`, 'info');
          }
        }
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        addLog(`Error checking scan status: ${errorMessage}`, 'error');
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [scanId, visible]);
  
  const addLog = (message: string, type: 'info' | 'warning' | 'error' | 'success') => {
    setLogs(prev => [
      ...prev,
      {
        timestamp: new Date().toISOString(),
        message,
        type
      }
    ]);
  };
  
  const getIconForType = (type: string) => {
    switch (type) {
      case 'info':
        return <Terminal className="h-4 w-4 text-blue-400" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-400" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-400" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      default:
        return <Terminal className="h-4 w-4 text-accent" />;
    }
  };
  
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  if (!visible) return null;

  return (
    <div className="mt-6 bg-secondary-dark rounded-xl p-4 border border-secondary shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-medium text-accent flex items-center">
          <Terminal className="h-5 w-5 mr-2" />
          Scan Logs
        </h3>
        {isLoading && (
          <div className="flex items-center text-accent/70 text-sm">
            <Clock className="h-4 w-4 animate-pulse mr-1" />
            <span>Updating...</span>
          </div>
        )}
      </div>
      
      <div className="bg-primary/50 rounded-lg p-3 h-96 overflow-y-auto font-mono text-sm">
        {logs.length === 0 ? (
          <div className="text-accent/50 text-center py-4">No logs available</div>
        ) : (
          <div className="space-y-1">
            {logs.map((log, index) => (
              <div 
                key={index} 
                className={`flex items-start py-1 ${
                  index % 2 === 0 ? 'bg-primary/20' : ''
                } rounded px-2`}
              >
                <div className="mr-2 mt-1">{getIconForType(log.type)}</div>
                <div className="flex-1">
                  <span className="text-accent/50 mr-2">[{formatTimestamp(log.timestamp)}]</span>
                  <span className={`
                    ${log.type === 'error' ? 'text-red-400' : ''}
                    ${log.type === 'warning' ? 'text-yellow-400' : ''}
                    ${log.type === 'success' ? 'text-green-400' : ''}
                    ${log.type === 'info' ? 'text-accent' : ''}
                  `}>
                    {log.message}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ScanLogs;
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface ScanProgressProps {
  status: string;
  progress: number;
  stage?: string;
  error?: string;
}

function ScanProgress({ status, progress, stage, error }: ScanProgressProps) {
  const getStatusIcon = () => {
    if (status === 'completed') {
      return <CheckCircle className="h-5 w-5 text-green-400" />;
    } else if (status === 'failed') {
      return <AlertCircle className="h-5 w-5 text-red-400" />;
    } else {
      return <Loader2 className="h-5 w-5 animate-spin text-accent" />;
    }
  };

  const getStatusColorClass = () => {
    if (status === 'completed') {
      return 'bg-green-500/20 text-green-400';
    } else if (status === 'failed') {
      return 'bg-red-500/20 text-red-400';
    } else {
      return 'bg-highlight/20 text-accent';
    }
  };

  return (
    <div className="mt-4 space-y-3">
      {}
      <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${getStatusColorClass()}`}>
        {getStatusIcon()}
        <span>{status}</span>
      </div>

      {}
      <div className="w-full bg-secondary rounded-full h-2.5 overflow-hidden">
        <div 
          className="h-full bg-highlight transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {}
      {stage && (
        <div className="text-sm text-text-secondary">
          Current stage: <span className="text-accent font-medium">{stage}</span>
        </div>
      )}

      {}
      {error && (
        <div className="text-sm text-red-400 bg-red-400/10 p-2 rounded">
          {error}
        </div>
      )}
    </div>
  );
}

export default ScanProgress;
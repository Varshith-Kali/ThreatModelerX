import { useState } from 'react';
import { Activity, AlertTriangle, FileSearch, BookOpen } from 'lucide-react';
import Dashboard from './components/Dashboard';
import ScanForm from './components/ScanForm';
import FindingsView from './components/FindingsView';
import ThreatView from './components/ThreatView';
import TrainingSection from './components/TrainingSection';

type View = 'dashboard' | 'scan' | 'findings' | 'threats' | 'training';

function App() {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);

  const handleScanComplete = (scanId: string) => {
    setSelectedScanId(scanId);
    setCurrentView('findings');
  };

  return (
    <div className="min-h-screen bg-primary text-text-primary flex flex-col">
      <header className="bg-secondary py-4 px-6 border-b border-highlight shadow-md">
        <div className="flex justify-between items-center max-w-screen-2xl mx-auto w-full">
          <div className="flex items-center">
            <img src="/logo.png" alt="ThreatModelerX" className="h-8 w-8 mr-3 brightness-0 invert" />
            <h1 className="text-2xl font-bold text-accent-DEFAULT">ThreatModelerX</h1>
          </div>
          <nav className="flex space-x-4">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${currentView === 'dashboard'
                ? 'bg-primary-light text-accent'
                : 'text-text-secondary hover:text-accent hover:bg-primary-light/50'
                }`}
            >
              <Activity className="h-5 w-5" />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setCurrentView('scan')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${currentView === 'scan'
                ? 'bg-primary-light text-accent'
                : 'text-text-secondary hover:text-accent hover:bg-primary-light/50'
                }`}
            >
              <FileSearch className="h-5 w-5" />
              <span>New Scan</span>
            </button>
            <button
              onClick={() => setCurrentView('findings')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${currentView === 'findings'
                ? 'bg-primary-light text-accent'
                : 'text-text-secondary hover:text-accent hover:bg-primary-light/50'
                }`}
            >
              <AlertTriangle className="h-5 w-5" />
              <span>Findings</span>
            </button>
            <button
              onClick={() => setCurrentView('threats')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${currentView === 'threats'
                ? 'bg-primary-light text-accent'
                : 'text-text-secondary hover:text-accent hover:bg-primary-light/50'
                }`}
            >
              <AlertTriangle className="h-5 w-5" />
              <span>Threats</span>
            </button>
            <button
              onClick={() => setCurrentView('training')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${currentView === 'training'
                ? 'bg-primary-light text-accent'
                : 'text-text-secondary hover:text-accent hover:bg-primary-light/50'
                }`}
            >
              <BookOpen className="h-5 w-5" />
              <span>Training</span>
            </button>
          </nav>
        </div>
      </header>

      <main className="w-full flex-1 py-8 px-6">
        <div className="max-w-screen-2xl mx-auto w-full">
          {currentView === 'dashboard' && <Dashboard onViewScan={(scanId) => {
            setSelectedScanId(scanId);
            setCurrentView('findings');
          }} />}
          {currentView === 'scan' && <ScanForm onScanComplete={handleScanComplete} />}
          {currentView === 'findings' && <FindingsView scanId={selectedScanId} />}
          {currentView === 'threats' && <ThreatView scanId={selectedScanId} />}
          {currentView === 'training' && <TrainingSection />}
        </div>
      </main>
    </div>
  );
}

export default App;

import React from 'react';
import { ShieldAlert, Activity, Cpu, Database, LogOut } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onLogout, userRole }) {
  return (
    <header className="sticky top-0 z-50 border-b border-sentinel-800 bg-sentinel-950/80 backdrop-blur-md px-6 py-3">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20 border border-blue-400/30">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-black tracking-wider text-white font-mono">
                SENTINEL<span className="text-blue-500">.AI</span>
              </span>
              <span className="flex items-center space-x-1 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>SOC CONSOLE</span>
              </span>
            </div>
            <div className="text-[10px] text-gray-500 font-mono tracking-tight">
              RASRO ORCHESTRATOR
            </div>
          </div>
        </div>

        {/* Center Tabs */}
        <nav className="flex space-x-1 bg-sentinel-900/90 border border-sentinel-800 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
              activeTab === 'dashboard'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-sentinel-800/50'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>EXECUTIVE SOC</span>
          </button>

          <button
            onClick={() => setActiveTab('simulation')}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
              activeTab === 'simulation'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-sentinel-800/50'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>THREAT SIMULATOR</span>
          </button>

          <button
            onClick={() => setActiveTab('activities')}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
              activeTab === 'activities'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-sentinel-800/50'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>AUDIT TELEMETRY</span>
          </button>
          <button onClick={() => setActiveTab('research')}
            className={`px-4 py-1.5 rounded-md text-xs font-semibold ${activeTab === 'research' ? 'bg-blue-600 text-white' : 'text-gray-400'}`}>
            RESEARCH RESULTS
          </button>
        </nav>

        {/* Right Info & Logout */}
        <div className="flex items-center space-x-4">
          <div className="text-right border-r border-sentinel-800 pr-4">
            <div className="text-[10px] text-gray-500 font-mono uppercase">SECURITY TIER</div>
            <div className="text-xs font-mono font-bold text-cyan-400">{userRole}</div>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center space-x-1 text-xs bg-red-500/10 text-red-400 border border-red-500/30 px-3 py-1.5 rounded hover:bg-red-500/20 transition font-mono"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>REVOKE SESSION</span>
          </button>
        </div>
      </div>
    </header>
  );
}
import React from 'react';
import { ShieldCheck, AlertOctagon, Lock, Eye, AlertTriangle } from 'lucide-react';

export default function DecisionPanel({ action = 'ALLOW', riskScore = 0 }) {
  const getActionTheme = (act) => {
    switch (act) {
      case 'ALLOW':
        return {
          icon: ShieldCheck,
          color: 'text-emerald-400',
          border: 'border-emerald-500/30',
          bg: 'bg-emerald-950/20',
          desc: 'Telemetry consistent with normal enterprise baseline. Continued access recommended.'
        };
      case 'MONITOR':
        return {
          icon: Eye,
          color: 'text-yellow-400',
          border: 'border-yellow-500/30',
          bg: 'bg-yellow-950/20',
          desc: 'Anomalous deviation noted. Closer session monitoring recommended.'
        };
      case 'STEP_UP_AUTH':
        return {
          icon: Lock,
          color: 'text-amber-400',
          border: 'border-amber-500/30',
          bg: 'bg-amber-950/20',
          desc: 'Suspicious privilege/time violation. Additional authentication recommended.'
        };
      case 'RESTRICT':
        return {
          icon: AlertTriangle,
          color: 'text-orange-400',
          border: 'border-orange-500/30',
          bg: 'bg-orange-950/20',
          desc: 'Exfiltration footprint identified. File-access and egress restrictions recommended.'
        };
      case 'REVOKE':
        return {
          icon: AlertOctagon,
          color: 'text-red-400',
          border: 'border-red-500/40',
          bg: 'bg-red-950/30',
          desc: 'High-severity malicious insider data exfiltration detected. Session revocation recommended.'
        };
      default:
        return {
          icon: ShieldCheck,
          color: 'text-gray-400',
          border: 'border-gray-800',
          bg: 'bg-gray-900',
          desc: 'Pending evaluation.'
        };
    }
  };

  const theme = getActionTheme(action);
  const Icon = theme.icon;

  return (
    <div className={`p-5 rounded-xl border ${theme.border} ${theme.bg} relative overflow-hidden backdrop-blur-md`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className="text-[10px] font-mono tracking-widest uppercase text-gray-400">
            STRATEGIC RESPONSE ORCHESTRATION (RASRO)
          </span>
          <div className="text-xs text-gray-500 font-mono">Adaptive Stackelberg Game Engine</div>
        </div>
        <div className="px-2 py-0.5 rounded text-[10px] font-mono border border-gray-700 bg-sentinel-950/60 text-gray-300">
          CLOSED-LOOP
        </div>
      </div>

      <div className="flex items-center space-x-3 mb-4">
        <div className={`p-2.5 rounded-lg border ${theme.border} bg-sentinel-950/60`}>
          <Icon className={`w-6 h-6 ${theme.color}`} />
        </div>
        <div>
          <div className="text-[10px] text-gray-400 font-mono">RECOMMENDED SECURITY DECISION</div>
          <div className={`text-xl font-black font-mono tracking-wide ${theme.color}`}>
            {action}
          </div>
        </div>
      </div>

      <div className="p-3 bg-sentinel-950/80 rounded-lg border border-sentinel-800 mb-3">
        <div className="flex justify-between items-center text-xs font-mono mb-1">
          <span className="text-gray-400">RISK INDEX</span>
          <span className={`font-bold ${riskScore >= 70 ? 'text-red-400' : riskScore >= 40 ? 'text-yellow-400' : 'text-emerald-400'}`}>
            {riskScore}/100
          </span>
        </div>
        <div className="w-full bg-sentinel-850 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              riskScore >= 70 ? 'bg-red-500' : riskScore >= 40 ? 'bg-yellow-500' : 'bg-emerald-500'
            }`}
            style={{ width: `${riskScore}%` }}
          />
        </div>
      </div>

      <p className="text-[11px] text-gray-400 font-mono leading-relaxed">
        {theme.desc}
      </p>
    </div>
  );
}
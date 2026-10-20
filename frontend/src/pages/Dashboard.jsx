import React, { useEffect, useState } from 'react';
import client from '../api/client';
import StatCard from '../components/StatCard';
import ShapChart from '../components/ShapChart';
import DecisionPanel from '../components/DecisionPanel';
import { Users, Activity, AlertTriangle, ShieldAlert, Cpu, RefreshCw } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, alertsRes, incRes] = await Promise.all([
        client.get('/api/analytics/dashboard-stats'),
        client.get('/api/alerts/'),
        client.get('/api/incidents/')
      ]);
      setStats(statsRes.data);
      setAlerts(alertsRes.data);
      setIncidents(incRes.data);
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center space-y-3 font-mono text-xs text-gray-500">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        <span>CONNECTING TO POSTGRESQL & RASRO ORCHESTRATOR...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <p className="text-sm text-gray-400">{stats?.model_source} · {stats?.enforcement_mode}</p>
      <div className="text-sm border border-gray-800 rounded p-3">Latest AAS: {Number(stats?.latest_assessment?.aas || 0).toFixed(3)} · RES: {stats?.latest_assessment?.res_available ? Number(stats.latest_assessment.res).toFixed(3) : 'N/A'} · Previous defence: {stats?.latest_assessment?.previous_defence || 'UNKNOWN'}</div>
      {/* Top SOC Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <StatCard
          label="Active Users"
          value={stats?.total_users || 0}
          icon={Users}
          subtext="Standard Enterprise Pool"
        />
        <StatCard
          label="Telemetry Ingested"
          value={stats?.total_activities || 0}
          icon={Activity}
          subtext="Session-level Records"
        />
        <StatCard
          label="Threat Incidents"
          value={stats?.total_incidents || 0}
          icon={ShieldAlert}
          alert={stats?.total_incidents > 0}
          subtext="Adaptive Exfiltrations"
        />
        <StatCard
          label="Security Alerts"
          value={stats?.total_alerts || 0}
          icon={AlertTriangle}
          alert={stats?.total_alerts > 0}
          subtext="Actionable Triggers"
        />
        <StatCard
          label="System Risk Avg"
          value={`${stats?.average_risk || 0}%`}
          icon={Cpu}
          subtext="Anomaly Normalized"
        />
      </div>

      {/* Main Analysis Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: SHAP XAI & Incident Feeds */}
        <div className="lg:col-span-2 space-y-6">
          <div className="border border-sentinel-800 rounded-xl p-5 bg-sentinel-900/60 backdrop-blur-md">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-gray-300">
                  EXPLAINABLE AI ENGINE: SHAP FEATURE ATTRIBUTION
                </h3>
                <p className="text-[11px] text-gray-500 font-mono">
                  Identifies precise behavioural features driving Isolation Forest / One-Class SVM anomaly evaluations.
                </p>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800 px-2 py-0.5 rounded">
                TREE SHAP
              </span>
            </div>
            <ShapChart attributions={stats?.latest_assessment?.shap_attributions} />
          </div>

          {/* Active Incidents Table */}
          <div className="border border-sentinel-800 rounded-xl p-5 bg-sentinel-900/60 backdrop-blur-md">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-gray-300">
                MALICIOUS INSIDER INCIDENT LOG
              </h3>
              <span className="text-[10px] font-mono text-red-400">{incidents.length} FLAGGED</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-[11px]">
                <thead>
                  <tr className="border-b border-sentinel-800 text-gray-500">
                    <th className="pb-2">TIMESTAMP</th>
                    <th className="pb-2">TARGET USER</th>
                    <th className="pb-2">THREAT VECTOR</th>
                    <th className="pb-2 text-right">RISK SCORE</th>
                    <th className="pb-2 text-right">DECISION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-sentinel-850">
                  {incidents.slice(0, 5).map((inc) => (
                    <tr key={inc.id} className="hover:bg-sentinel-850/40 transition-colors">
                      <td className="py-2.5 text-gray-400">{new Date(inc.timestamp).toLocaleTimeString()}</td>
                      <td className="py-2.5 text-blue-400 font-bold">User #{inc.user_id}</td>
                      <td className="py-2.5 text-gray-300">{inc.threat_type}</td>
                      <td className="py-2.5 text-right font-bold text-red-400">{inc.risk_score}</td>
                      <td className="py-2.5 text-right">
                        <span className="px-2 py-0.5 rounded border border-red-500/30 bg-red-950/30 text-red-300 text-[10px]">
                          {inc.enforced_action}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {incidents.length === 0 && (
                    <tr>
                      <td colSpan="5" className="py-6 text-center text-gray-500">
                        No active malicious insider incidents recorded. System in nominal state.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Stackelberg Game Intelligence & Alert Stream */}
        <div className="space-y-6">
          <DecisionPanel
            action={stats?.latest_assessment?.action}
            riskScore={stats?.latest_assessment?.risk_score || 0}
          />

          <div className="border border-sentinel-800 rounded-xl p-5 bg-sentinel-900/60 backdrop-blur-md">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-gray-300">
                REAL-TIME AUDIT ALERTS
              </h3>
              <span className="h-2 w-2 rounded-full bg-yellow-400 animate-ping"></span>
            </div>
            <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
              {alerts.slice(0, 6).map((al) => (
                <div
                  key={al.id}
                  className="p-3 bg-sentinel-850/50 rounded-lg border border-sentinel-800/80 font-mono text-[11px]"
                >
                  <div className="flex justify-between font-bold mb-1">
                    <span className={al.severity === 'CRITICAL' ? 'text-red-400' : 'text-yellow-400'}>
                      [{al.severity}]
                    </span>
                    <span className="text-gray-400">Risk {al.risk_score}</span>
                  </div>
                  <div className="text-gray-300 text-[10px] leading-relaxed">
                    User #{al.user_id} triggered response: <span className="text-cyan-400 font-bold">{al.recommended_action}</span>
                  </div>
                </div>
              ))}
              {alerts.length === 0 && (
                <div className="text-xs font-mono text-gray-500 py-4 text-center">
                  No alerts generated yet.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
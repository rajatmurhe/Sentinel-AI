import React, { useState } from 'react';
import client from '../api/client';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Play, Sliders, ShieldAlert, CheckCircle2, ArrowRight } from 'lucide-react';

export default function Simulation() {
  const [mode, setMode] = useState('manual'); // 'manual' or 'preset'

  // Preset Scenario States
  const [presetScenario, setPresetScenario] = useState('DATA_EXFILTRATION');
  const [presetUserId, setPresetUserId] = useState(3);

  // Manual Custom Input States
  const [manualData, setManualData] = useState({
    login_hour: 2,
    files_accessed: 85,
    sensitive_files_accessed: 20,
    bytes_transferred_mb: 1650,
    failed_logins: 2,
    privilege_level: 2,
    session_duration_min: 360,
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Run Preset Threat Batch
  const runPresetSimulation = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await client.post('/api/analytics/simulate-threat', {
        user_id: parseInt(presetUserId),
        scenario: presetScenario,
        iterations: 8,
        seed: 0,
      });
      setResults(res.data.executions);
    } catch (err) {
      setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Analysis failed. Check the inputs and retry.');
    } finally {
      setLoading(false);
    }
  };

  // Run Custom Manual Telemetry Injection
  const runManualInjection = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // Direct call to analyze single custom vector
      const res = await client.post('/api/activities/analyze', manualData);
      setResults([res.data.assessment]);
    } catch (err) {
      setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Analysis failed. Check the inputs and retry.');
    } finally {
      setLoading(false);
    }
  };

  const loadNormalPreset = () => {
    setManualData({
      login_hour: 11,
      files_accessed: 8,
      sensitive_files_accessed: 0,
      bytes_transferred_mb: 18,
      failed_logins: 0,
      privilege_level: 0,
      session_duration_min: 120,
    });
  };

  const loadExfiltrationPreset = () => {
    setManualData({
      login_hour: 3,
      files_accessed: 95,
      sensitive_files_accessed: 28,
      bytes_transferred_mb: 2400,
      failed_logins: 3,
      privilege_level: 2,
      session_duration_min: 420,
    });
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {error && <p role="alert" className="text-red-400">{error}</p>}
      <p className="text-sm text-gray-400">Synthetic demonstration detector. Security actions are recommendations; attack outcomes are simulated.</p>
      {/* Mode Selector */}
      <div className="flex space-x-2 border-b border-sentinel-800 pb-4">
        <button
          onClick={() => setMode('manual')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            mode === 'manual'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              : 'bg-sentinel-900 text-gray-400 hover:text-white border border-sentinel-800'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>LIVE MANUAL TELEMETRY INJECTOR (CUSTOM INPUTS)</span>
        </button>

        <button
          onClick={() => setMode('preset')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-mono font-bold transition-all ${
            mode === 'preset'
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
              : 'bg-sentinel-900 text-gray-400 hover:text-white border border-sentinel-800'
          }`}
        >
          <Play className="w-4 h-4" />
          <span>MULTI-CYCLE ATTACK SIMULATION (AUTOMATED)</span>
        </button>
      </div>

      {/* MANUAL MODE */}
      {mode === 'manual' && (
        <div className="border border-sentinel-800 rounded-xl p-6 bg-sentinel-900/60 backdrop-blur-md">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
                Custom User Session Telemetry Form
              </h2>
              <p className="text-[11px] font-mono text-gray-400 mt-1">
                Enter any raw activity attributes to evaluate how Isolation Forest, One-Class SVM, SHAP, and Stackelberg respond.
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                type="button"
                onClick={loadNormalPreset}
                className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded hover:bg-emerald-500/20"
              >
                Populate Normal Values
              </button>
              <button
                type="button"
                onClick={loadExfiltrationPreset}
                className="text-[10px] font-mono bg-red-500/10 text-red-400 border border-red-500/30 px-3 py-1.5 rounded hover:bg-red-500/20"
              >
                Populate Exfiltration Values
              </button>
            </div>
          </div>

          <form onSubmit={runManualInjection} className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div>
              <label className="block text-gray-400 mb-1">LOGIN HOUR (0-23 hrs)</label>
              <input
                type="number"
                min="0"
                max="23"
                value={manualData.login_hour}
                onChange={(e) => setManualData({ ...manualData, login_hour: parseFloat(e.target.value) })}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-gray-500">Normal: 8-18 | Malicious: 0-5 AM</span>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">TOTAL FILES ACCESSED</label>
              <input
                type="number"
                min="0"
                value={manualData.files_accessed}
                onChange={(e) => setManualData({ ...manualData, files_accessed: parseFloat(e.target.value) })}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-gray-500">Normal: 5-25 | Malicious: 50-150+</span>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">SENSITIVE FILES ACCESSED</label>
              <input
                type="number"
                min="0"
                value={manualData.sensitive_files_accessed}
                onChange={(e) => setManualData({ ...manualData, sensitive_files_accessed: parseFloat(e.target.value) })}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-gray-500">Normal: 0-2 | Malicious: 10-40+</span>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">BYTES TRANSFERRED (MB)</label>
              <input
                type="number"
                step="any"
                min="0"
                value={manualData.bytes_transferred_mb}
                onChange={(e) => setManualData({ ...manualData, bytes_transferred_mb: parseFloat(e.target.value) })}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-gray-500">Normal: 5-50 MB | Malicious: &gt;500 MB</span>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">FAILED LOGIN ATTEMPTS</label>
              <input
                type="number"
                min="0"
                value={manualData.failed_logins}
                onChange={(e) => setManualData({ ...manualData, failed_logins: parseFloat(e.target.value) })}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              />
              <span className="text-[10px] text-gray-500">Normal: 0 | Malicious: 2-6</span>
            </div>

            <div>
              <label className="block text-gray-400 mb-1">PRIVILEGE LEVEL</label>
              <select
                value={manualData.privilege_level}
                onChange={(e) => setManualData({ ...manualData, privilege_level: parseFloat(e.target.value) })}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
              >
                <option value={0}>0 - Standard Employee User</option>
                <option value={1}>1 - Elevated Analyst</option>
                <option value={2}>2 - High Admin / System Root</option>
              </select>
            </div>

            <div className="md:col-span-3 pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-lg transition shadow-lg shadow-blue-600/30 flex items-center justify-center space-x-2"
              >
                {loading ? 'Evaluating Model Inferences...' : 'Inject Telemetry & Run Analysis'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* PRESET MODE */}
      {mode === 'preset' && (
        <div className="border border-sentinel-800 rounded-xl p-6 bg-sentinel-900/60 backdrop-blur-md">
          <h2 className="text-sm font-mono font-bold text-white uppercase tracking-wider mb-2">
            Automated Attack Sequence Generator
          </h2>
          <p className="text-[11px] font-mono text-gray-400 mb-6">
            Executes recurring multi-cycle attacks to demonstrate adaptive evasion and game-theoretic responses.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 font-mono text-xs">
            <div>
              <label className="block uppercase text-gray-400 mb-1">ATTACK SCENARIO</label>
              <select
                value={presetScenario}
                onChange={(e) => setPresetScenario(e.target.value)}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white"
              >
                <option value="DATA_EXFILTRATION">Massive Data Exfiltration (Off-Hours Burst)</option>
                <option value="ADAPTIVE_EVASION">Adaptive Evasion (Progressive Low-and-Slow)</option>
                <option value="NORMAL">Routine Enterprise Baseline</option>
              </select>
            </div>
            <div>
              <label className="block uppercase text-gray-400 mb-1">TARGET USER ACCOUNT ID</label>
              <input
                type="number"
                value={presetUserId}
                onChange={(e) => setPresetUserId(e.target.value)}
                className="w-full bg-sentinel-850 border border-sentinel-800 rounded px-3 py-2 text-white"
              />
            </div>
          </div>

          <button
            onClick={runPresetSimulation}
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-mono font-bold py-2.5 rounded-lg transition shadow-lg shadow-indigo-600/30"
          >
            {loading ? 'Simulating Iterations...' : 'Execute Multi-Cycle Injection'}
          </button>
        </div>
      )}

      {/* REAL-TIME PIPELINE VERDICT OUTPUT */}
      {results && (
        <div className="border border-sentinel-800 rounded-xl p-6 bg-sentinel-900/60 backdrop-blur-md space-y-4">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-gray-300 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>PIPELINE EXECUTION OUTPUT & MODEL VERDICTS</span>
          </h3>

          {results.length > 1 && <div className="h-72">
            <ResponsiveContainer width="100%" height="100%"><LineChart data={results.map((r, i) => ({ turn: i + 1, risk: r.risk_score, AAS: r.adaptive_metrics?.adaptation_score_aas, RES: r.adaptive_metrics?.res_available ? r.adaptive_metrics.response_effectiveness_res : null }))}>
              <XAxis dataKey="turn" /><YAxis yAxisId="risk" domain={[0,100]} /><YAxis yAxisId="metric" orientation="right" domain={[0,1]} /><Tooltip /><Legend />
              <Line yAxisId="risk" dataKey="risk" stroke="#f87171" /><Line yAxisId="metric" dataKey="AAS" stroke="#60a5fa" /><Line yAxisId="metric" dataKey="RES" stroke="#34d399" />
            </LineChart></ResponsiveContainer>
          </div>}
          <div className="space-y-3">
            {results.map((res, i) => (
              <div
                key={i}
                className="p-4 bg-sentinel-850/60 rounded-lg border border-sentinel-800 text-xs font-mono flex flex-col md:flex-row justify-between items-start md:items-center space-y-3 md:space-y-0"
              >
                <div>
                  <div className="font-bold text-white flex items-center space-x-2">
                    <span className="text-blue-400">Execution #{i + 1}</span>
                    <span className="text-gray-500">•</span>
                    <span>Target User #{res.user_id}</span>
                  </div>
                  <div className="text-gray-400 text-[11px] mt-1 flex space-x-3">
                    <span>
                      IForest Anomaly:{' '}
                      <span className={res.iforest_anomaly ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                        {String(res.iforest_anomaly).toUpperCase()}
                      </span>
                    </span>
                    <span>•</span>
                    <span>
                      OCSVM Anomaly:{' '}
                      <span className={res.ocsvm_anomaly ? 'text-red-400 font-bold' : 'text-emerald-400'}>
                        {String(res.ocsvm_anomaly).toUpperCase()}
                      </span>
                    </span>
                  </div>
                </div>

                <div className="text-gray-300 space-y-1">
                  <div>AAS: {res.adaptive_metrics?.adaptation_score_aas?.toFixed(3)} · RES: {res.adaptive_metrics?.res_available ? res.adaptive_metrics.response_effectiveness_res.toFixed(3) : 'N/A'}</div>
                  <div>Previous defence: {res.adaptive_metrics?.previous_defence}</div>
                  <div>State: {res.simulated_attacker_state || res.adaptive_metrics?.attacker_state}</div>
                  {res.behaviour && <div>Transfer: {res.behaviour.bytes_transferred_mb.toFixed(1)} MiB · Files: {res.behaviour.files_accessed.toFixed(1)} · Login: {res.behaviour.login_hour.toFixed(1)}h</div>}
                </div>
                <div className="flex items-center space-x-6 text-right">
                  <div>
                    <div className="text-[10px] text-gray-500 uppercase">CALCULATED RISK</div>
                    <div
                      className={`text-xl font-black ${
                        res.risk_score >= 70 ? 'text-red-400' : res.risk_score >= 40 ? 'text-yellow-400' : 'text-emerald-400'
                      }`}
                    >
                      {res.risk_score}/100
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] text-gray-500 uppercase">STACKELBERG DECISION</div>
                    <div className="px-2.5 py-1 rounded bg-sentinel-950 border border-blue-500/40 text-blue-400 font-bold">
                      {res.game_action}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="p-3 bg-sentinel-950/60 rounded border border-sentinel-800 text-[11px] font-mono text-gray-400 flex items-center justify-between">
            <span>Audit telemetry, alerts, and incident logs have been saved to the application database.</span>
            <a href="#" onClick={(e) => { e.preventDefault(); window.location.href = '/'; }} className="text-blue-400 hover:underline flex items-center space-x-1">
              <span>View On SOC Dashboard</span>
              <ArrowRight className="w-3 h-3" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
import React, { useEffect, useState } from 'react';
import client from '../api/client';

const metric = (row, key) => {
  const value = Number(row[`${key}_mean`]);
  const sd = Number(row[`${key}_std`]);
  return Number.isFinite(value) ? `${value.toFixed(4)} ± ${sd.toFixed(4)}` : 'Unavailable';
};

export default function Research() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [figures, setFigures] = useState([]);
  useEffect(() => {
    let cancelled = false;
    const urls = [];
    (async () => {
      try {
        const result = (await client.get('/api/research/results')).data;
        if (cancelled) return;
        setData(result);
        const images = [];
        for (const name of result.files.filter(name => name.endsWith('.png'))) {
          const response = await client.get(`/api/research/files/${name}`, { responseType: 'blob' });
          if (cancelled) return;
          const url = URL.createObjectURL(response.data);
          urls.push(url); images.push({ name, url });
        }
        if (!cancelled) setFigures(images);
      } catch (err) {
        if (!cancelled) setError(err.response?.data?.detail || 'Could not load research results.');
      }
    })();
    return () => { cancelled = true; urls.forEach(url => URL.revokeObjectURL(url)); };
  }, []);
  const download = async name => {
    try {
      const response = await client.get(`/api/research/files/${name}`, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const link = document.createElement('a'); link.href = url; link.download = name; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch { setError('Download failed. Please retry.'); }
  };
  return <div className="max-w-7xl mx-auto p-6 space-y-6">
    <h1 className="text-2xl font-bold">Research results</h1>
    {error && <p role="alert" className="text-red-400">{error}</p>}
    {!data && !error && <p>Loading saved experiment results…</p>}
    {data && <>
      <p className="text-gray-400">{data.note}</p>
      <p className="text-sm text-gray-300">CERT r4.2 · Seeds: {data.manifest.seeds?.join(', ') || 'See report'} · Protocol: {data.manifest.evaluation_mode || 'Original temporal evaluation'}</p>
      <section className="border border-gray-800 rounded-xl p-5 overflow-x-auto">
        <h2 className="text-lg font-semibold mb-4">CERT detection — mean ± standard deviation</h2>
        <table className="w-full text-sm text-left"><thead><tr>
          {['Model', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'AP', 'FPR'].map(x => <th key={x} className="p-2">{x}</th>)}
        </tr></thead><tbody>{data.detection.map(row => <tr key={row.model} className="border-t border-gray-800">
          <td className="p-2">{row.model}</td>{['precision','recall','f1','roc_auc','average_precision','false_positive_rate'].map(key => <td key={key} className="p-2 whitespace-nowrap">{metric(row,key)}</td>)}
        </tr>)}</tbody></table>
      </section>
      <section className="border border-gray-800 rounded-xl p-5 overflow-x-auto">
        <h2 className="text-lg font-semibold mb-4">Simulated adaptive attacker — separate from CERT</h2>
        <table className="w-full text-sm text-left"><thead><tr>
          {['Policy','Attack success','Risk after defence','AAS','RES'].map(x => <th key={x} className="p-2">{x}</th>)}
        </tr></thead><tbody>{data.adaptive.map(row => <tr key={row.variant} className="border-t border-gray-800"><td className="p-2">{row.variant}</td>
          {['attack_success_rate','risk_after_defence','aas','res'].map(key => <td key={key} className="p-2 whitespace-nowrap">{metric(row,key)}</td>)}
        </tr>)}</tbody></table>
      </section>
      <div className="grid gap-4">{figures.map(({name,url}) => <img key={name} src={url} alt={name.replaceAll('-',' ')} className="w-full rounded-lg bg-white" />)}</div>
      <section><h2 className="text-lg font-semibold mb-3">Download evidence</h2><div className="flex flex-wrap gap-3">{data.files.map(name => <button key={name} onClick={() => download(name)} className="text-blue-300 border border-gray-700 rounded px-3 py-2 text-sm">{name}</button>)}</div></section>
    </>}
  </div>;
}

// frontend/src/pages/Backtesting.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar, ComposedChart,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ReferenceLine, ReferenceDot
} from 'recharts';
import { Play, History, TrendingDown, BarChart3, RefreshCw, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { getToken } from '../services/authService';

const API = 'http://localhost:5000/api/backtest';
const fetchAPI = async (path, options = {}) => {
  const token = getToken();
  const res = await fetch(`${API}${path}`, {
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.error || 'Request failed'); }
  return res.json();
};

const STRATEGIES = [
  { id: 'buy_and_hold', label: 'Buy & Hold', desc: 'Buy at start, hold until end' },
  { id: 'moving_average', label: 'Moving Average Crossover', desc: 'Buy on golden cross, sell on death cross' },
  { id: 'risk_based', label: 'Risk-Based', desc: 'Sell when risk score exceeds threshold' },
  { id: 'mean_reversion', label: 'Mean Reversion', desc: 'Buy oversold, sell when price reverts to mean' },
];

// ==================== BACKTEST TAB ====================
const BacktestPanel = ({ stocks }) => {
  const [symbol, setSymbol] = useState('AAPL');
  const [strategy, setStrategy] = useState('buy_and_hold');
  const [days, setDays] = useState(365);
  const [capital, setCapital] = useState(10000);
  const [params, setParams] = useState({ short_window: 20, long_window: 50, risk_threshold: 0.6, lookback: 20, z_entry: -1.0, z_exit: 0.5 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
useEffect(() => {
    if (stocks.length > 0 && !stocks.includes(symbol)) setSymbol(stocks[0]);
  }, [stocks]);

  const runBacktest = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await fetchAPI('/run', {
        method: 'POST',
        body: JSON.stringify({ symbol, strategy, start_days_ago: days, initial_capital: capital, params }),
      });
      setResult(res);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const gridColor = '#e5e7eb';
  const axisColor = '#6b7280';

  const m = result?.metrics;

  return (
    <div>
      {/* Config Panel */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Stock</label>
          <select value={symbol} onChange={e => setSymbol(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
            {stocks.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Strategy</label>
          <select value={strategy} onChange={e => setStrategy(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
            {STRATEGIES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Period</label>
          <select value={days} onChange={e => setDays(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
            {[90, 180, 365, 730].map(d => <option key={d} value={d}>{d < 365 ? `${d}D` : `${d / 365}Y`}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Capital ($)</label>
          <input type="number" value={capital} onChange={e => setCapital(Number(e.target.value))} min={100}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
        </div>
      </div>

      {/* Strategy-specific params */}
      {strategy === 'moving_average' && (
        <div className="flex gap-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Short MA</label>
            <input type="number" value={params.short_window} onChange={e => setParams({ ...params, short_window: Number(e.target.value) })}
              className="w-24 px-3 py-1.5 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Long MA</label>
            <input type="number" value={params.long_window} onChange={e => setParams({ ...params, long_window: Number(e.target.value) })}
              className="w-24 px-3 py-1.5 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
          </div>
        </div>
      )}
      {strategy === 'risk_based' && (
        <div className="flex gap-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Risk Threshold</label>
            <input type="number" step="0.05" value={params.risk_threshold} onChange={e => setParams({ ...params, risk_threshold: Number(e.target.value) })}
              className="w-28 px-3 py-1.5 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
          </div>
        </div>
      )}
      {strategy === 'mean_reversion' && (
        <div className="flex gap-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Lookback</label>
            <input type="number" value={params.lookback} onChange={e => setParams({ ...params, lookback: Number(e.target.value) })}
              className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Z Entry</label>
            <input type="number" step="0.1" value={params.z_entry} onChange={e => setParams({ ...params, z_entry: Number(e.target.value) })}
              className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Z Exit</label>
            <input type="number" step="0.1" value={params.z_exit} onChange={e => setParams({ ...params, z_exit: Number(e.target.value) })}
              className="w-20 px-3 py-1.5 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm" />
          </div>
        </div>
      )}

      <button onClick={runBacktest} disabled={loading}
        className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm flex items-center gap-2 disabled:opacity-50 mb-6">
        {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
        {loading ? 'Running...' : 'Run Backtest'}
      </button>

      {error && <div className="mb-5 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">{error}</div>}

      {result && !loading && (
        <>
          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
            <MetricCard label="Total Return" value={`${(m.total_return * 100).toFixed(1)}%`} color={m.total_return >= 0 ? 'green' : 'red'} />
            <MetricCard label="Annual Return" value={`${(m.annual_return * 100).toFixed(1)}%`} color={m.annual_return >= 0 ? 'green' : 'red'} />
            <MetricCard label="Max Drawdown" value={`${(m.max_drawdown * 100).toFixed(1)}%`} color="red" />
            <MetricCard label="Sharpe Ratio" value={m.sharpe_ratio.toFixed(2)} color={m.sharpe_ratio >= 1 ? 'green' : m.sharpe_ratio >= 0 ? 'neutral' : 'red'} />
            <MetricCard label="Sortino Ratio" value={m.sortino_ratio.toFixed(2)} />
            <MetricCard label="Annual Vol" value={`${(m.annual_volatility * 100).toFixed(1)}%`} />
            <MetricCard label="Win Rate" value={`${(m.win_rate * 100).toFixed(0)}%`} color={m.win_rate >= 0.5 ? 'green' : 'red'} />
            <MetricCard label="Total Trades" value={m.total_trades} />
            <MetricCard label="Final Equity" value={`$${m.final_equity.toLocaleString()}`} color={m.final_equity >= capital ? 'green' : 'red'} />
            <MetricCard label="vs Benchmark" value={`${((m.total_return - m.benchmark_return) * 100).toFixed(1)}%`}
              color={m.total_return >= m.benchmark_return ? 'green' : 'red'} />
          </div>

          {/* Equity Curve */}
          <h4 className="font-semibold text-gray-900 mb-3">Equity Curve vs Benchmark</h4>
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={result.equity_curve} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis dataKey="date" tickFormatter={v => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                stroke={axisColor} tick={{ fontSize: 11 }} tickLine={false} />
              <YAxis stroke={axisColor} tick={{ fontSize: 12 }} tickLine={false} tickFormatter={v => `$${(v / 1000).toFixed(1)}k`} />
              <Tooltip content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                return (
                  <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-4 py-3 text-sm">
                    <p className="font-medium text-gray-900 mb-1">{label ? new Date(label).toLocaleDateString() : ''}</p>
                    {payload.map((p, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
                        <span className="text-gray-500">{p.name}:</span>
                        <span className="font-semibold text-gray-900">${p.value?.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                );
              }} />
              <Legend />
              <Area type="monotone" dataKey="equity" name="Strategy" stroke="#3b82f6" strokeWidth={2} fill="url(#eqGrad)" dot={false} />
              <Line type="monotone" dataKey="benchmark" name="Buy & Hold" stroke="#6b7280" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
              {/* Trade markers */}
              {result.trades.filter(t => t.action === 'BUY').map((t, i) => {
                const point = result.equity_curve.find(e => e.date === t.date);
                if (!point) return null;
                return <ReferenceDot key={`b${i}`} x={t.date} y={point.equity} r={5} fill="#10b981" stroke="white" strokeWidth={2} />;
              })}
              {result.trades.filter(t => t.action === 'SELL').map((t, i) => {
                const point = result.equity_curve.find(e => e.date === t.date);
                if (!point) return null;
                return <ReferenceDot key={`s${i}`} x={t.date} y={point.equity} r={5} fill="#ef4444" stroke="white" strokeWidth={2} />;
              })}
            </ComposedChart>
          </ResponsiveContainer>
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500 inline-block" /> Buy</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> Sell</span>
          </div>

          {/* Trade Log */}
          {result.trades.length > 0 && (
            <div className="mt-6">
              <h4 className="font-semibold text-gray-900 mb-3">Trade Log ({result.trades.length})</h4>
              <div className="overflow-x-auto max-h-60 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Date</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Action</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Price</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Shares</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {result.trades.map((t, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-2 text-gray-700">{new Date(t.date).toLocaleDateString()}</td>
                        <td className="px-4 py-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${
                            t.action === 'BUY' ? 'bg-green-100 text-green-700'
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {t.action === 'BUY' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                            {t.action}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-gray-700">${t.price}</td>
                        <td className="px-4 py-2 text-gray-700">{t.shares || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};


// ==================== HISTORICAL ANALYSIS TAB ====================
const HistoricalAnalysisPanel = ({ stocks }) => {
  const [symbol, setSymbol] = useState('AAPL');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
useEffect(() => {
    if (stocks.length > 0 && !stocks.includes(symbol)) setSymbol(stocks[0]);
  }, [stocks]);

  const load = useCallback(async () => {
    if (!symbol) return;
    setLoading(true); setError('');
    try {
      const res = await fetchAPI(`/historical-analysis/${symbol}?days=365`);
      setData(res);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [symbol]);

  useEffect(() => { load(); }, [load]);

  const gridColor = '#e5e7eb';
  const axisColor = '#6b7280';

  return (
    <div>
      <div className="flex items-center gap-3 mb-5">
        <select value={symbol} onChange={e => setSymbol(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
          {stocks.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {loading && <LoadingSpinner text={`Analyzing ${symbol}...`} />}
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">{error}</div>}

      {data && !loading && (
        <>
          {/* Period Returns */}
          <div className="grid grid-cols-5 gap-3 mb-6">
            {Object.entries(data.period_returns).map(([label, val]) => (
              <MetricCard key={label} label={label.toUpperCase()} value={val != null ? `${(val * 100).toFixed(1)}%` : 'N/A'}
                color={val != null ? (val >= 0 ? 'green' : 'red') : 'neutral'} />
            ))}
          </div>

          {/* Drawdown Chart */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3">Drawdown from Peak</h4>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={data.drawdown_analysis.drawdown_curve} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="date" tickFormatter={v => new Date(v).toLocaleDateString('en-US', { month: 'short' })}
                  stroke={axisColor} tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis stroke={axisColor} tick={{ fontSize: 12 }} tickLine={false} tickFormatter={v => `${v}%`} />
                <Tooltip content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  return (
                    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
                      <p className="font-medium">{new Date(label).toLocaleDateString()}</p>
                      <p className="text-red-600">Drawdown: {payload[0].value}%</p>
                    </div>
                  );
                }} />
                <Area type="monotone" dataKey="drawdown" stroke="#ef4444" fill="rgba(239,68,68,0.15)" dot={false} />
                <ReferenceLine y={0} stroke={axisColor} strokeDasharray="3 3" />
              </AreaChart>
            </ResponsiveContainer>
            <div className="flex gap-6 mt-2 text-sm text-gray-600">
              <span>Max Drawdown: <strong className="text-red-600">{(data.drawdown_analysis.max_drawdown * 100).toFixed(1)}%</strong></span>
              <span>Current: <strong>{(data.drawdown_analysis.current_drawdown * 100).toFixed(1)}%</strong></span>
            </div>
          </div>

          {/* Rolling Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">30-Day Rolling Return</h4>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={data.rolling_metrics} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis dataKey="date" tickFormatter={v => new Date(v).toLocaleDateString('en-US', { month: 'short' })}
                    stroke={axisColor} tick={{ fontSize: 11 }} tickLine={false} />
                  <YAxis stroke={axisColor} tick={{ fontSize: 12 }} tickLine={false} tickFormatter={v => `${v}%`} />
                  <Tooltip content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null;
                    return (
                      <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
                        <p className="font-medium">{new Date(label).toLocaleDateString()}</p>
                        <p>Return: {payload[0]?.value}%</p>
                      </div>
                    );
                  }} />
                  <ReferenceLine y={0} stroke={axisColor} strokeDasharray="3 3" />
                  <Area type="monotone" dataKey="return_30d" stroke="#3b82f6" fill="rgba(59,130,246,0.1)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">30-Day Rolling Volatility</h4>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data.rolling_metrics} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis dataKey="date" tickFormatter={v => new Date(v).toLocaleDateString('en-US', { month: 'short' })}
                    stroke={axisColor} tick={{ fontSize: 11 }} tickLine={false} />
                  <YAxis stroke={axisColor} tick={{ fontSize: 12 }} tickLine={false} tickFormatter={v => `${v}%`} />
                  <Tooltip content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null;
                    return (
                      <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
                        <p className="font-medium">{new Date(label).toLocaleDateString()}</p>
                        <p>Vol: {payload[0]?.value}%</p>
                      </div>
                    );
                  }} />
                  <Line type="monotone" dataKey="volatility_30d" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Return Distribution */}
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3">Daily Return Distribution</h4>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={data.return_distribution.histogram} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="bin" stroke={axisColor} tick={{ fontSize: 11 }} tickLine={false} tickFormatter={v => `${v}%`} />
                <YAxis stroke={axisColor} tick={{ fontSize: 12 }} tickLine={false} />
                <Tooltip content={({ active, payload }) => {
                  if (!active || !payload?.length) return null;
                  return (
                    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
                      <p>Return: {payload[0]?.payload?.bin}%</p>
                      <p>Count: {payload[0]?.value}</p>
                    </div>
                  );
                }} />
                <ReferenceLine x={0} stroke={axisColor} />
                <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                  {data.return_distribution.histogram.map((entry, i) => (
                    <Cell key={i} fill={entry.bin >= 0 ? ('rgba(59,130,246,0.5)') : ('rgba(239,68,68,0.4)')} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-4 md:grid-cols-7 gap-2 mt-3">
              {[
                ['Mean', `${data.return_distribution.stats.mean.toFixed(3)}%`],
                ['Std Dev', `${data.return_distribution.stats.std.toFixed(3)}%`],
                ['Skew', data.return_distribution.stats.skew.toFixed(2)],
                ['Kurtosis', data.return_distribution.stats.kurtosis.toFixed(2)],
                ['Up Days', `${data.return_distribution.stats.positive_days}`],
                ['Down Days', `${data.return_distribution.stats.negative_days}`],
                ['Total', `${data.return_distribution.stats.total_days}`],
              ].map(([l, v]) => (
                <div key={l} className="text-center">
                  <p className="text-xs text-gray-500">{l}</p>
                  <p className="text-sm font-semibold text-gray-900">{v}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Best / Worst Days */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-green-600 mb-2 flex items-center gap-1.5">
                <ArrowUpRight className="w-4 h-4" /> Best Days
              </h4>
              {data.best_worst_days.best.map((d, i) => (
                <div key={i} className="flex justify-between py-2 border-b border-gray-100 text-sm">
                  <span className="text-gray-700">{new Date(d.date).toLocaleDateString()}</span>
                  <span className="font-semibold text-green-600">+{d.return_pct}%</span>
                </div>
              ))}
            </div>
            <div>
              <h4 className="font-semibold text-red-600 mb-2 flex items-center gap-1.5">
                <ArrowDownRight className="w-4 h-4" /> Worst Days
              </h4>
              {data.best_worst_days.worst.map((d, i) => (
                <div key={i} className="flex justify-between py-2 border-b border-gray-100 text-sm">
                  <span className="text-gray-700">{new Date(d.date).toLocaleDateString()}</span>
                  <span className="font-semibold text-red-600">{d.return_pct}%</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};


// ==================== SHARED COMPONENTS ====================
const MetricCard = ({ label, value, color = 'neutral' }) => (
  <div className="bg-gray-50 rounded-lg p-3">
    <p className="text-xs text-gray-500">{label}</p>
    <p className={`text-lg font-bold mt-0.5 ${
      color === 'green' ? 'text-green-600'
        : color === 'red' ? 'text-red-600'
        : 'text-gray-900'
    }`}>{value}</p>
  </div>
);

const LoadingSpinner = ({ text }) => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
      <p className="mt-3 text-sm text-gray-500">{text}</p>
    </div>
  </div>
);


// ==================== MAIN PAGE ====================
const Backtesting = () => {
  const [activeTab, setActiveTab] = useState('backtest');
  const [stocks, setStocks] = useState([]);

  useEffect(() => {
    const loadStocks = async () => {
      try {
        const token = getToken();
        const res = await fetch('http://localhost:5000/api/risk-scores', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const d = await res.json();
        if (d.data) {
          setStocks([...new Set(d.data.map(s => s.symbol))].sort());
        }
      } catch (e) { console.error(e); }
    };
    loadStocks();
  }, []);

  const tabItems = [
    { id: 'backtest', label: 'Strategy Backtest', icon: Play },
    { id: 'analysis', label: 'Historical Analysis', icon: History },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <h1 className="text-3xl font-bold text-gray-900">Backtesting Engine</h1>
        <p className="text-gray-600 mt-1">
          Test trading strategies against historical data and analyze stock performance
        </p>
      </div>

      <div className="bg-white rounded-lg shadow transition-colors">
        <div className="border-b border-gray-200">
          <nav className="flex">
            {tabItems.map(tab => {
              const Icon = tab.icon;
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-5 py-3.5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}>
                  <Icon className="w-4 h-4" />{tab.label}
                </button>
              );
            })}
          </nav>
        </div>
        <div className="p-6">
          {activeTab === 'backtest' && <BacktestPanel stocks={stocks} />}
          {activeTab === 'analysis' && <HistoricalAnalysisPanel stocks={stocks} />}
        </div>
      </div>
    </div>
  );
};

export default Backtesting;
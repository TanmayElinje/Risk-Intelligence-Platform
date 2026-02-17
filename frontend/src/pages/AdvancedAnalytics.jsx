// frontend/src/pages/AdvancedAnalytics.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  ScatterChart, Scatter, AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  Cell, ReferenceLine
} from 'recharts';
import { Activity, TrendingUp, Shield, PieChart, RefreshCw, ChevronDown } from 'lucide-react';
import { getToken } from '../services/authService';

const API = 'http://localhost:5000/api/advanced';

const fetchAPI = async (path) => {
  const token = getToken();
  const res = await fetch(`${API}${path}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || 'Request failed');
  }
  return res.json();
};

// ==================== TAB NAVIGATION ====================
const tabs = [
  { id: 'correlation', label: 'Correlation Matrix', icon: Activity },
  { id: 'montecarlo', label: 'Monte Carlo', icon: TrendingUp },
  { id: 'var', label: 'Value at Risk', icon: Shield },
  { id: 'optimize', label: 'Optimization', icon: PieChart },
];

// ==================== CORRELATION HEATMAP ====================
const CorrelationMatrix = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [days, setDays] = useState(90);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await fetchAPI(`/correlation?days=${days}`);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner text="Computing correlations..." />;
  if (error) return <ErrorMsg text={error} onRetry={load} />;
  if (!data) return null;

  const { symbols, matrix } = data;
  const n = symbols.length;

  // Color scale: -1 (red) → 0 (white/gray) → 1 (blue)
  const getColor = (val) => {
    if (val >= 0) {
      const intensity = Math.min(val, 1);
      return `rgba(59, 130, 246, ${0.05 + intensity * 0.7})`;
    } else {
      const intensity = Math.min(Math.abs(val), 1);
      return `rgba(239, 68, 68, ${0.05 + intensity * 0.7})`;
    }
  };

  const cellSize = Math.min(48, Math.max(28, Math.floor(600 / n)));

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <TimeRangeSelector value={days} onChange={setDays} options={[30, 60, 90, 180, 365]} />
        <span className="text-sm text-gray-500">{data.data_points} data points</span>
      </div>

      <div className="overflow-x-auto">
        <div className="inline-block">
          {/* Header row */}
          <div className="flex">
            <div style={{ width: cellSize * 1.8 }} />
            {symbols.map(s => (
              <div
                key={s}
                style={{ width: cellSize, height: cellSize }}
                className="flex items-center justify-center text-xs font-semibold text-gray-600 -rotate-45 origin-center"
              >
                {s}
              </div>
            ))}
          </div>

          {/* Matrix rows */}
          {symbols.map((rowSymbol, i) => (
            <div key={rowSymbol} className="flex items-center">
              <div
                style={{ width: cellSize * 1.8 }}
                className="text-xs font-semibold text-gray-700 text-right pr-2 truncate"
              >
                {rowSymbol}
              </div>
              {matrix[i].map((val, j) => {
                
                return (
                  <div
                    key={j}
                    style={{
                      width: cellSize,
                      height: cellSize,
                      backgroundColor: getColor(val),
                    }}
                    className="border border-gray-100 flex items-center justify-center text-xs font-medium cursor-default transition-all hover:ring-1 hover:ring-blue-400"
                    title={`${rowSymbol} × ${symbols[j]}: ${val.toFixed(3)}`}
                  >
                    <span className={`${i === j ? 'text-gray-400' : 'text-gray-800'}`}>
                      {cellSize >= 36 ? val.toFixed(2) : ''}
                    </span>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(239, 68, 68, 0.6)' }} />
          Negative
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-gray-200" />
          Neutral
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgba(59, 130, 246, 0.6)' }} />
          Positive
        </div>
      </div>
    </div>
  );
};


// ==================== MONTE CARLO ====================
const MonteCarlo = () => {
  const [symbol, setSymbol] = useState('AAPL');
  const [forecastDays, setForecastDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stocks, setStocks] = useState([]);
// Load stock list
  useEffect(() => {
    const loadStocks = async () => {
      try {
        const token = getToken();
        const res = await fetch('http://localhost:5000/api/risk-scores', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const d = await res.json();
        if (d.data) {
          const list = [...new Map(d.data.map(s => [s.symbol, s.symbol])).values()].sort();
          setStocks(list);
          if (list.length > 0 && !list.includes(symbol)) setSymbol(list[0]);
        }
      } catch (e) { console.error(e); }
    };
    loadStocks();
  }, []);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await fetchAPI(`/monte-carlo/${symbol}?forecast_days=${forecastDays}&simulations=1000`);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [symbol, forecastDays]);

  useEffect(() => { if (symbol) runSimulation(); }, [runSimulation]);

  // Build chart data
  const chartData = data ? data.dates.map((date, i) => ({
    date,
    p5: data.simulations.percentile_5[i],
    p25: data.simulations.percentile_25[i],
    p50: data.simulations.percentile_50[i],
    p75: data.simulations.percentile_75[i],
    p95: data.simulations.percentile_95[i],
  })) : [];

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <select
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
        >
          {stocks.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={forecastDays}
          onChange={(e) => setForecastDays(Number(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm"
        >
          {[7, 14, 30, 60, 90].map(d => <option key={d} value={d}>{d} Days</option>)}
        </select>
        <button onClick={runSimulation} disabled={loading}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg flex items-center gap-1.5 disabled:opacity-50">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Run
        </button>
      </div>

      {loading && <LoadingSpinner text={`Simulating ${symbol}...`} />}
      {error && <ErrorMsg text={error} onRetry={runSimulation} />}

      {data && !loading && (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
            <StatCard label="Current Price" value={`$${data.current_price}`} />
            <StatCard label="Median Forecast" value={`$${data.final_prices.median}`}
              color={data.final_prices.median >= data.current_price ? 'green' : 'red'} />
            <StatCard label="95th Percentile" value={`$${data.final_prices.p95}`} color="green" />
            <StatCard label="5th Percentile" value={`$${data.final_prices.p5}`} color="red" />
          </div>

          {/* Cone Chart */}
          <ResponsiveContainer width="100%" height={380}>
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={'#e5e7eb'} />
              <XAxis dataKey="date" tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                stroke={'#6b7280'} tick={{ fontSize: 12 }} tickLine={false} />
              <YAxis stroke={'#6b7280'} tick={{ fontSize: 12 }} tickLine={false}
                tickFormatter={(v) => `$${v}`} domain={['auto', 'auto']} />
              <Tooltip content={({ active, payload, label }) => {
                if (!active || !payload?.length) return null;
                return (
                  <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-4 py-3 text-sm">
                    <p className="font-medium text-gray-900 mb-1">{label ? new Date(label).toLocaleDateString() : ''}</p>
                    {payload.filter(p => p.dataKey === 'p50' || p.dataKey === 'p5' || p.dataKey === 'p95').map((p, i) => (
                      <div key={i} className="text-gray-600">
                        {p.dataKey === 'p50' ? 'Median' : p.dataKey === 'p5' ? '5th %ile' : '95th %ile'}: <strong className="text-gray-900">${p.value}</strong>
                      </div>
                    ))}
                  </div>
                );
              }} />
              <Area type="monotone" dataKey="p95" stroke="none" fill={'rgba(59,130,246,0.06)'} name="95th %ile" />
              <Area type="monotone" dataKey="p75" stroke="none" fill={'rgba(59,130,246,0.1)'} name="75th %ile" />
              <Area type="monotone" dataKey="p25" stroke="none" fill={'rgba(59,130,246,0.1)'} name="25th %ile" />
              <Area type="monotone" dataKey="p5" stroke="none" fill={'rgba(59,130,246,0.06)'} name="5th %ile" />
              <Line type="monotone" dataKey="p50" stroke="#3b82f6" strokeWidth={2.5} dot={false} name="Median" />
              <Line type="monotone" dataKey="p95" stroke="#93c5fd" strokeWidth={1} strokeDasharray="4 4" dot={false} />
              <Line type="monotone" dataKey="p5" stroke="#93c5fd" strokeWidth={1} strokeDasharray="4 4" dot={false} />
              <ReferenceLine y={data.current_price} stroke={'#9ca3af'} strokeDasharray="3 3" label={{ value: 'Current', fill: '#6b7280', fontSize: 11 }} />
            </AreaChart>
          </ResponsiveContainer>

          <div className="mt-3 text-xs text-gray-500">
            {data.num_simulations} simulations | Annual Volatility: {(data.annual_volatility * 100).toFixed(1)}% | Shaded regions show 5th–95th percentile range
          </div>
        </>
      )}
    </div>
  );
};


// ==================== VALUE AT RISK ====================
const ValueAtRisk = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [confidence, setConfidence] = useState(0.95);
const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await fetchAPI(`/var?confidence=${confidence}&days=90`);
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [confidence]);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner text="Computing Value at Risk..." />;
  if (error) return <ErrorMsg text={error} onRetry={load} />;
  if (!data) return null;

  const chartData = data.stocks.map(s => ({
    symbol: s.symbol,
    var: Math.abs(s.var_pct * 100),
    es: Math.abs(s.es_pct * 100),
    volatility: s.annual_volatility * 100,
    sharpe: s.sharpe_ratio,
  })).sort((a, b) => b.var - a.var);

  return (
    <div>
      <div className="flex items-center gap-3 mb-5">
        <select value={confidence} onChange={(e) => setConfidence(Number(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm">
          <option value={0.90}>90% Confidence</option>
          <option value={0.95}>95% Confidence</option>
          <option value={0.99}>99% Confidence</option>
        </select>
      </div>

      {/* Portfolio VaR summary */}
      {data.portfolio && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <StatCard label="Portfolio VaR (1-day)" value={`${(data.portfolio.var_pct * 100).toFixed(2)}%`} color="red" />
          <StatCard label="Portfolio VaR ($)" value={`$${Math.abs(data.portfolio.var_dollar).toLocaleString()}`} color="red" />
          <StatCard label="Expected Shortfall" value={`${(data.portfolio.es_pct * 100).toFixed(2)}%`} color="red" />
          <StatCard label="Diversification Benefit" value={`${(data.portfolio.diversification_benefit * 100).toFixed(1)}%`} color="green" />
        </div>
      )}

      {/* VaR Bar Chart */}
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={'#e5e7eb'} />
          <XAxis dataKey="symbol" stroke={'#6b7280'} tick={{ fontSize: 11 }} />
          <YAxis stroke={'#6b7280'} tick={{ fontSize: 12 }} tickFormatter={(v) => `${v.toFixed(1)}%`} />
          <Tooltip content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0]?.payload;
            return (
              <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-4 py-3 text-sm">
                <p className="font-semibold text-gray-900 mb-1">{d.symbol}</p>
                <p className="text-red-600">VaR: {d.var.toFixed(2)}%</p>
                <p className="text-orange-600">ES: {d.es.toFixed(2)}%</p>
                <p className="text-gray-600">Vol: {d.volatility.toFixed(1)}%</p>
                <p className="text-gray-600">Sharpe: {d.sharpe.toFixed(2)}</p>
              </div>
            );
          }} />
          <Legend />
          <Bar dataKey="var" name="Value at Risk (%)" fill="#ef4444" radius={[4, 4, 0, 0]} />
          <Bar dataKey="es" name="Expected Shortfall (%)" fill="#f97316" radius={[4, 4, 0, 0]} opacity={0.7} />
        </BarChart>
      </ResponsiveContainer>

      <p className="mt-3 text-xs text-gray-500">
        {confidence * 100}% confidence, 1-day horizon, ${data.portfolio_value?.toLocaleString()} portfolio value
      </p>
    </div>
  );
};


// ==================== PORTFOLIO OPTIMIZATION ====================
const PortfolioOptimization = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await fetchAPI('/optimize?days=180');
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSpinner text="Optimizing portfolio..." />;
  if (error) return <ErrorMsg text={error} onRetry={load} />;
  if (!data) return null;

  // Efficient frontier scatter
  const frontierData = data.efficient_frontier.map(p => ({
    volatility: (p.annual_volatility * 100),
    return: (p.annual_return * 100),
  }));

  // Key portfolios
  const keyPortfolios = [
    { ...data.equal_weight, name: 'Equal Weight', color: '#6b7280' },
    { ...data.min_variance, name: 'Min Variance', color: '#3b82f6' },
    { ...data.max_sharpe, name: 'Max Sharpe', color: '#10b981' },
  ];

  // Weight comparison chart
  const weightData = data.symbols.map(s => ({
    symbol: s,
    equal: (data.equal_weight.weights[s] || 0) * 100,
    minVar: (data.min_variance.weights[s] || 0) * 100,
    maxSharpe: (data.max_sharpe.weights[s] || 0) * 100,
  }));

  return (
    <div>
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {keyPortfolios.map(p => (
          <div key={p.name} className="bg-gray-50 rounded-lg p-4 border-l-4" style={{ borderLeftColor: p.color }}>
            <h4 className="font-semibold text-gray-900 text-sm mb-2">{p.name}</h4>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <p className="text-gray-500 text-xs">Return</p>
                <p className={`font-semibold ${p.annual_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(p.annual_return * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Volatility</p>
                <p className="font-semibold text-gray-900">{(p.annual_volatility * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Sharpe</p>
                <p className="font-semibold text-gray-900">{p.sharpe_ratio.toFixed(2)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Efficient Frontier */}
      <h4 className="font-semibold text-gray-900 mb-3">Efficient Frontier</h4>
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={'#e5e7eb'} />
          <XAxis dataKey="volatility" name="Volatility" stroke={'#6b7280'}
            tick={{ fontSize: 12 }} tickFormatter={(v) => `${v.toFixed(0)}%`} label={{ value: 'Volatility (%)', position: 'bottom', offset: -5, fill: '#6b7280', fontSize: 12 }} />
          <YAxis dataKey="return" name="Return" stroke={'#6b7280'}
            tick={{ fontSize: 12 }} tickFormatter={(v) => `${v.toFixed(0)}%`} label={{ value: 'Return (%)', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 12 }} />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ payload }) => {
            if (!payload?.length) return null;
            const d = payload[0]?.payload;
            return (
              <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs">
                <p>Return: {d.return?.toFixed(2)}%</p>
                <p>Volatility: {d.volatility?.toFixed(2)}%</p>
              </div>
            );
          }} />
          <Scatter data={frontierData} fill={'#d1d5db'} r={2} />
          {/* Key portfolio markers */}
          {keyPortfolios.map(p => (
            <Scatter key={p.name} data={[{
              volatility: p.annual_volatility * 100,
              return: p.annual_return * 100,
            }]} fill={p.color} r={8} name={p.name} />
          ))}
          <Legend />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Weight Allocation Comparison */}
      <h4 className="font-semibold text-gray-900 mb-3 mt-6">Weight Allocation Comparison</h4>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={weightData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={'#e5e7eb'} />
          <XAxis dataKey="symbol" stroke={'#6b7280'} tick={{ fontSize: 11 }} />
          <YAxis stroke={'#6b7280'} tick={{ fontSize: 12 }} tickFormatter={(v) => `${v.toFixed(0)}%`} />
          <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
          <Legend />
          <Bar dataKey="equal" name="Equal Weight" fill="#6b7280" radius={[2, 2, 0, 0]} />
          <Bar dataKey="minVar" name="Min Variance" fill="#3b82f6" radius={[2, 2, 0, 0]} />
          <Bar dataKey="maxSharpe" name="Max Sharpe" fill="#10b981" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};


// ==================== SHARED COMPONENTS ====================
const LoadingSpinner = ({ text }) => (
  <div className="flex items-center justify-center min-h-[200px]">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      <p className="mt-3 text-sm text-gray-500">{text}</p>
    </div>
  </div>
);

const ErrorMsg = ({ text, onRetry }) => (
  <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
    {text}
    {onRetry && (
      <button onClick={onRetry} className="ml-3 underline hover:no-underline">Retry</button>
    )}
  </div>
);

const StatCard = ({ label, value, color }) => (
  <div className="bg-gray-50 rounded-lg p-3">
    <p className="text-xs text-gray-500">{label}</p>
    <p className={`text-lg font-bold mt-0.5 ${
      color === 'green' ? 'text-green-600'
        : color === 'red' ? 'text-red-600'
        : 'text-gray-900'
    }`}>{value}</p>
  </div>
);

const TimeRangeSelector = ({ value, onChange, options }) => (
  <div className="flex bg-gray-100 rounded-lg p-1">
    {options.map(d => (
      <button key={d} onClick={() => onChange(d)}
        className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
          value === d ? 'bg-blue-600 text-white shadow-sm'
            : 'text-gray-600 hover:text-gray-900'
        }`}>
        {d}D
      </button>
    ))}
  </div>
);


// ==================== MAIN PAGE ====================
const AdvancedAnalytics = () => {
  const [activeTab, setActiveTab] = useState('correlation');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <h1 className="text-3xl font-bold text-gray-900">Advanced Analytics</h1>
        <p className="text-gray-600 mt-1">
          Quantitative risk analysis, simulations, and portfolio optimization
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow transition-colors">
        <div className="border-b border-gray-200">
          <nav className="flex overflow-x-auto">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-5 py-3.5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'correlation' && <CorrelationMatrix />}
          {activeTab === 'montecarlo' && <MonteCarlo />}
          {activeTab === 'var' && <ValueAtRisk />}
          {activeTab === 'optimize' && <PortfolioOptimization />}
        </div>
      </div>
    </div>
  );
};

export default AdvancedAnalytics;
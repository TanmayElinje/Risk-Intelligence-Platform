// frontend/src/pages/HistoricalData.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ComposedChart, ReferenceLine
} from 'recharts';
import { TrendingUp, Calendar, Search, X, Activity, BarChart3, ChevronDown } from 'lucide-react';
import { getToken } from '../services/authService';

// ==================== TIME RANGES ====================
const TIME_RANGES = [
  { label: '7D', value: 7 },
  { label: '30D', value: 30 },
  { label: '90D', value: 90 },
  { label: '6M', value: 180 },
  { label: '1Y', value: 365 },
];

// ==================== CUSTOM TOOLTIP ====================
const ChartTooltip = ({ active, payload, label, formatter }) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-4 py-3 text-sm">
      <p className="font-medium text-gray-900 mb-1.5">
        {label ? new Date(label).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''}
      </p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 py-0.5">
          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-gray-600">{entry.name}:</span>
          <span className="font-semibold text-gray-900">
            {formatter ? formatter(entry.value, entry.name) : (
              typeof entry.value === 'number' ? entry.value.toFixed(entry.name === 'Volume' ? 0 : 4) : entry.value
            )}
          </span>
        </div>
      ))}
    </div>
  );
};

// ==================== STOCK SELECTOR ====================
const StockSelector = ({ value, onChange, stocks, loading }) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const wrapperRef = useRef(null);
  const inputRef = useRef(null);

  const filtered = query.trim()
    ? stocks.filter(s => s.symbol.includes(query.toUpperCase()))
    : stocks;

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    setHighlightIndex(-1);
  }, [query]);

  const selectStock = (symbol) => {
    onChange(symbol);
    setQuery('');
    setIsOpen(false);
  };

  const handleKeyDown = (e) => {
    if (!isOpen && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      setIsOpen(true);
      e.preventDefault();
      return;
    }
    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightIndex(prev => Math.min(prev + 1, filtered.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightIndex >= 0 && highlightIndex < filtered.length) {
          selectStock(filtered[highlightIndex].symbol);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  const getRiskColor = (level) => {
    const colors = {
      high: 'bg-red-100 text-red-700',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-green-100 text-green-700',
    };
    return colors[level] || '';
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-xs">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={isOpen ? query : ''}
          onChange={(e) => {
            setQuery(e.target.value.toUpperCase());
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          className="w-full pl-9 pr-10 py-2.5 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors text-sm"
          placeholder={value || 'Select stock...'}
          autoComplete="off"
        />
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
        >
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {loading ? (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="px-4 py-3 text-sm text-gray-500 text-center">
              No stocks matching "{query}"
            </div>
          ) : (
            filtered.map((stock, index) => (
              <button
                key={stock.symbol}
                type="button"
                onClick={() => selectStock(stock.symbol)}
                className={`w-full text-left px-4 py-2.5 flex items-center justify-between transition-colors text-sm ${
                  index === highlightIndex ? 'bg-blue-50'
                    : stock.symbol === value ? 'bg-gray-50'
                    : 'hover:bg-gray-50'
                }`}
              >
                <span className={`font-semibold ${stock.symbol === value ? 'text-blue-600' : 'text-gray-900'}`}>
                  {stock.symbol}
                </span>
                {stock.risk_level && (
                  <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${getRiskColor(stock.risk_level)}`}>
                    {stock.risk_level.charAt(0).toUpperCase() + stock.risk_level.slice(1)}
                  </span>
                )}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};


// ==================== CHART CARD WRAPPER ====================
const ChartCard = ({ title, icon: Icon, children, subtitle, className = '' }) => (
  <div className={`bg-white rounded-lg shadow p-6 transition-colors ${className}`}>
    <div className="flex items-center justify-between mb-4">
      <div>
        <div className="flex items-center gap-2">
          {Icon && <Icon className="w-5 h-5 text-gray-500" />}
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
    {children}
  </div>
);


// ==================== MAIN PAGE ====================
const HistoricalData = () => {
  const [selectedStock, setSelectedStock] = useState('');
  const [timeRange, setTimeRange] = useState(90);
  const [stocks, setStocks] = useState([]);
  const [stocksLoading, setStocksLoading] = useState(true);

  // Chart data
  const [marketData, setMarketData] = useState([]);
  const [riskHistory, setRiskHistory] = useState([]);
  const [stockDetails, setStockDetails] = useState(null);
  const [chartsLoading, setChartsLoading] = useState(false);
  const [error, setError] = useState('');

  // Detect dark mode
// Chart colors that adapt to theme
  const colors = {
    grid: '#e5e7eb',
    axis: '#6b7280',
    price: '#3b82f6',
    priceFill: 'rgba(59, 130, 246, 0.1)',
    volume: '#818cf8',
    risk: '#ef4444',
    riskFill: 'rgba(239, 68, 68, 0.1)',
    volatility: '#f59e0b',
    sentiment: '#10b981',
    sentimentFill: 'rgba(16, 185, 129, 0.1)',
  };

  // Fetch stock list on mount
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const token = getToken();
        const response = await fetch('http://localhost:5000/api/risk-scores', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        if (data.data && Array.isArray(data.data)) {
          const stockList = [...new Map(
            data.data.map(s => [s.symbol, { symbol: s.symbol, risk_level: s.risk_level, risk_score: s.risk_score }])
          ).values()].sort((a, b) => a.symbol.localeCompare(b.symbol));
          setStocks(stockList);
          // Auto-select first stock
          if (stockList.length > 0 && !selectedStock) {
            setSelectedStock(stockList[0].symbol);
          }
        }
      } catch (err) {
        console.error('Error fetching stocks:', err);
      } finally {
        setStocksLoading(false);
      }
    };
    fetchStocks();
  }, []);

  // Fetch chart data when stock or time range changes
  const fetchChartData = useCallback(async () => {
    if (!selectedStock) return;

    setChartsLoading(true);
    setError('');

    try {
      const token = getToken();
      const headers = { 'Authorization': `Bearer ${token}` };

      const [marketRes, riskRes, detailsRes] = await Promise.all([
        fetch(`http://localhost:5000/api/market-features/${selectedStock}?days=${timeRange}`, { headers }),
        fetch(`http://localhost:5000/api/risk-history?symbol=${selectedStock}&days=${timeRange}`, { headers }),
        fetch(`http://localhost:5000/api/stock/${selectedStock}`, { headers }),
      ]);

      const [marketJson, riskJson, detailsJson] = await Promise.all([
        marketRes.json(),
        riskRes.json(),
        detailsRes.json(),
      ]);

      setMarketData(marketJson.data || []);
      setRiskHistory(riskJson.data || []);
      setStockDetails(detailsJson);

    } catch (err) {
      console.error('Error fetching chart data:', err);
      setError('Failed to load historical data. Please try again.');
    } finally {
      setChartsLoading(false);
    }
  }, [selectedStock, timeRange]);

  useEffect(() => {
    fetchChartData();
  }, [fetchChartData]);

  // Format helpers
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    if (timeRange <= 30) return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const formatPrice = (val) => {
    if (val == null) return '';
    return `$${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatVolume = (val) => {
    if (val == null) return '';
    if (val >= 1e9) return `${(val / 1e9).toFixed(1)}B`;
    if (val >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
    if (val >= 1e3) return `${(val / 1e3).toFixed(1)}K`;
    return val.toString();
  };

  // Compute price change stats
  const priceChange = marketData.length >= 2
    ? {
        value: marketData[marketData.length - 1]?.Close - marketData[0]?.Close,
        pct: ((marketData[marketData.length - 1]?.Close - marketData[0]?.Close) / marketData[0]?.Close) * 100,
      }
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Historical Data
            </h1>
            <p className="text-gray-600 mt-1">
              Visualize price, risk, volatility, and sentiment trends over time
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {/* Stock Selector */}
            <StockSelector
              value={selectedStock}
              onChange={setSelectedStock}
              stocks={stocks}
              loading={stocksLoading}
            />

            {/* Time Range Selector */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              {TIME_RANGES.map((range) => (
                <button
                  key={range.value}
                  onClick={() => setTimeRange(range.value)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                    timeRange === range.value
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Stats Bar */}
        {selectedStock && stockDetails && !chartsLoading && (
          <div className="mt-4 pt-4 border-t border-gray-200 flex flex-wrap gap-x-8 gap-y-2 text-sm">
            <div>
              <span className="text-gray-500">Symbol: </span>
              <span className="font-semibold text-gray-900">{selectedStock}</span>
            </div>
            {stockDetails.Close != null && (
              <div>
                <span className="text-gray-500">Last Price: </span>
                <span className="font-semibold text-gray-900">{formatPrice(stockDetails.Close)}</span>
              </div>
            )}
            {priceChange && (
              <div>
                <span className="text-gray-500">Period Change: </span>
                <span className={`font-semibold ${priceChange.value >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {priceChange.value >= 0 ? '+' : ''}{formatPrice(priceChange.value)} ({priceChange.pct >= 0 ? '+' : ''}{priceChange.pct.toFixed(2)}%)
                </span>
              </div>
            )}
            {stockDetails.risk_score != null && (
              <div>
                <span className="text-gray-500">Risk Score: </span>
                <span className={`font-semibold ${
                  stockDetails.risk_level === 'high' ? 'text-red-600'
                    : stockDetails.risk_level === 'medium' ? 'text-yellow-600'
                    : 'text-green-600'
                }`}>
                  {stockDetails.risk_score?.toFixed(3)} ({stockDetails.risk_level})
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Loading / Error States */}
      {chartsLoading && (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-3 text-gray-500 text-sm">Loading historical data for {selectedStock}...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {!chartsLoading && !error && selectedStock && (
        <>
          {/* Row 1: Price + Volume */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Price Chart - takes 2/3 */}
            <ChartCard
              title="Price History"
              icon={TrendingUp}
              subtitle={marketData.length > 0 ? `${marketData.length} data points` : 'No data available'}
              className="lg:col-span-2"
            >
              {marketData.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={marketData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={colors.price} stopOpacity={0.25} />
                        <stop offset="95%" stopColor={colors.price} stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                    <XAxis
                      dataKey="Date"
                      tickFormatter={formatDate}
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                      tickFormatter={(v) => `$${v}`}
                      domain={['auto', 'auto']}
                    />
                    <Tooltip content={<ChartTooltip formatter={(v, name) => name === 'Close' ? formatPrice(v) : v} />} />
                    <Area
                      type="monotone"
                      dataKey="Close"
                      name="Close"
                      stroke={colors.price}
                      strokeWidth={2}
                      fill="url(#priceGradient)"
                      dot={false}
                      activeDot={{ r: 4, fill: colors.price }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[320px] text-gray-400">
                  No price data available for this period
                </div>
              )}
            </ChartCard>

            {/* Volume Chart - takes 1/3 */}
            <ChartCard title="Trading Volume" icon={BarChart3}>
              {marketData.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={marketData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                    <XAxis
                      dataKey="Date"
                      tickFormatter={formatDate}
                      stroke={colors.axis}
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke={colors.axis}
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                      tickFormatter={formatVolume}
                    />
                    <Tooltip content={<ChartTooltip formatter={(v, name) => name === 'Volume' ? formatVolume(v) : v} />} />
                    <Bar
                      dataKey="Volume"
                      name="Volume"
                      fill={colors.volume}
                      radius={[2, 2, 0, 0]}
                      opacity={0.8}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[320px] text-gray-400">
                  No volume data
                </div>
              )}
            </ChartCard>
          </div>

          {/* Row 2: Risk Score + Volatility */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Risk Score Trend */}
            <ChartCard
              title="Risk Score Trend"
              icon={Activity}
              subtitle="How risk has evolved over time"
            >
              {riskHistory.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={riskHistory} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={colors.risk} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={colors.risk} stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={formatDate}
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[0, 1]}
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <ReferenceLine y={0.7} stroke={colors.risk} strokeDasharray="4 4" strokeOpacity={0.5} />
                    <ReferenceLine y={0.4} stroke={colors.volatility} strokeDasharray="4 4" strokeOpacity={0.5} />
                    <Area
                      type="monotone"
                      dataKey="risk_score"
                      name="Risk Score"
                      stroke={colors.risk}
                      strokeWidth={2}
                      fill="url(#riskGradient)"
                      dot={false}
                      activeDot={{ r: 4, fill: colors.risk }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[280px] text-gray-400">
                  No risk history data available for this period
                </div>
              )}
              {/* Risk level legend */}
              <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                <div className="flex items-center gap-1">
                  <div className="w-6 h-px bg-red-500 border-dashed"></div>
                  <span>High risk threshold (0.7)</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-6 h-px bg-yellow-500 border-dashed"></div>
                  <span>Medium risk threshold (0.4)</span>
                </div>
              </div>
            </ChartCard>

            {/* Volatility Trend */}
            <ChartCard
              title="Volatility (21-Day)"
              icon={Activity}
              subtitle="Annualized rolling volatility"
            >
              {marketData.some(d => d.volatility_21d != null) ? (
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={marketData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                    <XAxis
                      dataKey="Date"
                      tickFormatter={formatDate}
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                    />
                    <YAxis
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                      tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    />
                    <Tooltip content={<ChartTooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />} />
                    <Line
                      type="monotone"
                      dataKey="volatility_21d"
                      name="Volatility"
                      stroke={colors.volatility}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4, fill: colors.volatility }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[280px] text-gray-400">
                  No volatility data available (need at least 21 days)
                </div>
              )}
            </ChartCard>
          </div>

          {/* Row 3: Sentiment + Price & Volume Combined */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sentiment Trend */}
            <ChartCard
              title="Sentiment Trend"
              icon={TrendingUp}
              subtitle="Average news sentiment over time"
            >
              {stockDetails?.sentiment_history?.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={stockDetails.sentiment_history} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={colors.sentiment} stopOpacity={0.25} />
                        <stop offset="95%" stopColor={colors.sentiment} stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={formatDate}
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[-1, 1]}
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                    />
                    <Tooltip content={<ChartTooltip />} />
                    <ReferenceLine y={0} stroke={colors.axis} strokeDasharray="3 3" strokeOpacity={0.4} />
                    <Area
                      type="monotone"
                      dataKey="avg_sentiment"
                      name="Sentiment"
                      stroke={colors.sentiment}
                      strokeWidth={2}
                      fill="url(#sentimentGradient)"
                      dot={false}
                      activeDot={{ r: 4, fill: colors.sentiment }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[280px] text-gray-400">
                  No sentiment data available for this period
                </div>
              )}
            </ChartCard>

            {/* Price + Volume Combined */}
            <ChartCard
              title="Price & Volume Combined"
              icon={BarChart3}
              subtitle="Overlay of price action and trading volume"
            >
              {marketData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <ComposedChart data={marketData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                    <XAxis
                      dataKey="Date"
                      tickFormatter={formatDate}
                      stroke={colors.axis}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                    />
                    <YAxis
                      yAxisId="price"
                      stroke={colors.price}
                      tick={{ fontSize: 12 }}
                      tickLine={false}
                      tickFormatter={(v) => `$${v}`}
                      domain={['auto', 'auto']}
                    />
                    <YAxis
                      yAxisId="volume"
                      orientation="right"
                      stroke={colors.volume}
                      tick={{ fontSize: 11 }}
                      tickLine={false}
                      tickFormatter={formatVolume}
                    />
                    <Tooltip content={<ChartTooltip formatter={(v, name) =>
                      name === 'Close' ? formatPrice(v) : name === 'Volume' ? formatVolume(v) : v
                    } />} />
                    <Legend />
                    <Bar
                      yAxisId="volume"
                      dataKey="Volume"
                      name="Volume"
                      fill={colors.volume}
                      opacity={0.3}
                      radius={[2, 2, 0, 0]}
                    />
                    <Line
                      yAxisId="price"
                      type="monotone"
                      dataKey="Close"
                      name="Close"
                      stroke={colors.price}
                      strokeWidth={2}
                      dot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-[280px] text-gray-400">
                  No data available
                </div>
              )}
            </ChartCard>
          </div>
        </>
      )}

      {/* No stock selected state */}
      {!selectedStock && !stocksLoading && (
        <div className="bg-white rounded-lg shadow p-12 text-center transition-colors">
          <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Select a Stock
          </h3>
          <p className="text-gray-500">
            Choose a stock from the dropdown above to view its historical data
          </p>
        </div>
      )}
    </div>
  );
};

export default HistoricalData;
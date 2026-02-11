import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import { LineChart, Line, AreaChart, Area, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatDistanceToNow } from 'date-fns';

const StockDetails = () => {
  const { symbol } = useParams();
  const [loading, setLoading] = useState(true);
  const [stockData, setStockData] = useState(null);
  const [marketFeatures, setMarketFeatures] = useState([]);
  const [ragQuery, setRagQuery] = useState('');
  const [ragResponse, setRagResponse] = useState(null);
  const [ragLoading, setRagLoading] = useState(false);

  useEffect(() => {
    loadStockData();
  }, [symbol]);

  const loadStockData = async () => {
    try {
      setLoading(true);
      const [detailsRes, featuresRes] = await Promise.all([
        apiService.getStockDetails(symbol),
        apiService.getMarketFeatures(symbol, { days: 90 }),
      ]);

      setStockData(detailsRes.data);
      setMarketFeatures(featuresRes.data.data);
    } catch (error) {
      console.error('Failed to load stock data:', error);
      toast.error('Failed to load stock data');
    } finally {
      setLoading(false);
    }
  };

  const handleRAGQuery = async (e) => {
  e.preventDefault();
  if (!ragQuery.trim()) return;

  try {
    setRagLoading(true);
    
    console.log('Querying RAG for:', ragQuery, symbol);
    
    const response = await apiService.queryRAG(ragQuery, symbol);
    
    console.log('RAG response:', response.data);
    
    setRagResponse(response.data);
    toast.success('Answer generated!');
    
  } catch (error) {
    console.error('RAG query failed:', error);
    console.error('Error response:', error.response);
    
    let errorMsg = 'Failed to generate answer';
    
    if (error.code === 'ECONNABORTED') {
      // Timeout error
      errorMsg = 'The query is taking longer than expected. Please try a simpler question or wait a moment and try again.';
    } else if (error.response) {
      errorMsg = error.response.data?.explanation || 
                 error.response.data?.error || 
                 `Server error: ${error.response.status}`;
    } else if (error.request) {
      errorMsg = 'No response from server. Please check if backend is running.';
    } else {
      errorMsg = error.message;
    }
    
    toast.error(errorMsg);
    
    setRagResponse({
      explanation: errorMsg,
      sources: []
    });
  } finally {
    setRagLoading(false);
  }
};

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading stock details...</p>
        </div>
      </div>
    );
  }

  if (!stockData) {
    return (
      <div className="card text-center">
        <h2 className="text-xl font-bold text-red-600">Stock not found</h2>
        <Link to="/" className="text-blue-600 hover:text-blue-800 mt-4 inline-block">
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  // Prepare risk components data for radar chart
  const riskComponents = [
    { component: 'Volatility', value: stockData.norm_volatility * 100 || 0 },
    { component: 'Drawdown', value: stockData.norm_drawdown * 100 || 0 },
    { component: 'Sentiment', value: stockData.norm_sentiment * 100 || 0 },
    { component: 'Liquidity', value: stockData.norm_liquidity * 100 || 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link to="/" className="text-blue-600 hover:text-blue-800 inline-flex items-center">
        ← Back to Dashboard
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">{symbol}</h1>
            <p className="text-gray-600 mt-1">Last Price: ${stockData.Close?.toFixed(2)}</p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold mb-2">
              {stockData.risk_score?.toFixed(3)}
            </div>
            <span className={`badge badge-${stockData.risk_level?.toLowerCase()} text-lg px-4 py-2`}>
              {stockData.risk_level} Risk
            </span>
            <p className="text-sm text-gray-500 mt-2">Rank #{stockData.risk_rank}</p>
          </div>
        </div>

        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold mb-2">Risk Drivers:</h3>
          <p className="text-gray-700">{stockData.risk_drivers}</p>
        </div>
      </div>

      {/* Risk Components Radar */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Risk Component Breakdown</h2>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={riskComponents}>
            <PolarGrid />
            <PolarAngleAxis dataKey="component" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} />
            <Radar name="Risk Level" dataKey="value" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Score Trend */}
        {stockData.risk_history && stockData.risk_history.length > 0 && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Risk Score Trend</h2>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={stockData.risk_history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={(val) => new Date(val).toLocaleDateString()} />
                <YAxis domain={[0, 1]} />
                <Tooltip labelFormatter={(val) => new Date(val).toLocaleString()} />
                <Area type="monotone" dataKey="risk_score" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Volatility Trend */}
        {marketFeatures.length > 0 && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Volatility (21-day)</h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={marketFeatures}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="Date" tickFormatter={(val) => new Date(val).toLocaleDateString()} />
                <YAxis />
                <Tooltip labelFormatter={(val) => new Date(val).toLocaleString()} />
                <Line type="monotone" dataKey="volatility_21d" stroke="#f59e0b" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Price Trend */}
        {marketFeatures.length > 0 && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Price History</h2>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={marketFeatures}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="Date" tickFormatter={(val) => new Date(val).toLocaleDateString()} />
                <YAxis />
                <Tooltip labelFormatter={(val) => new Date(val).toLocaleString()} />
                <Area type="monotone" dataKey="Close" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Sentiment History */}
        {stockData.sentiment_history && stockData.sentiment_history.length > 0 && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">Sentiment Trend</h2>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={stockData.sentiment_history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <Line type="monotone" dataKey="avg_sentiment" stroke="#10b981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Recent Alerts */}
      {stockData.recent_alerts && stockData.recent_alerts.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Recent Alerts</h2>
          <div className="space-y-3">
            {stockData.recent_alerts.map((alert, idx) => (
              <div key={idx} className="border-l-4 border-red-500 bg-red-50 p-3 rounded-r">
                <div className="flex justify-between items-start mb-1">
                  <span className="font-bold text-red-700">{alert.alert_type?.replace('_', ' ')}</span>
                  <span className="text-xs text-gray-500">
                    {alert.timestamp && formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{alert.risk_drivers}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Q&A Section */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">🤖 Ask AI About {symbol}</h2>
        
        <form onSubmit={handleRAGQuery} className="mb-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              placeholder={`Ask anything about ${symbol}... (e.g., "Why is risk high?")`}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={ragLoading}
            />
            <button
              type="submit"
              disabled={ragLoading || !ragQuery.trim()}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
            >
              {ragLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Thinking...</span>
                </div>
              ) : 'Ask'}
            </button>
          </div>
        </form>

        {ragLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex items-center space-x-3">
              <div className="animate-spin h-6 w-6 border-3 border-blue-600 border-t-transparent rounded-full"></div>
              <div>
                <p className="font-semibold text-blue-900">AI is analyzing...</p>
                <p className="text-sm text-blue-700">This may take 30-60 seconds for the first query</p>
              </div>
            </div>
          </div>
        )}

        {ragResponse && !ragLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">Answer:</h3>
            <p className="text-gray-800 whitespace-pre-wrap">{ragResponse.explanation}</p>
            
            {ragResponse.sources && ragResponse.sources.length > 0 && (
              <div className="mt-4 pt-4 border-t border-blue-200">
                <h4 className="font-semibold text-sm text-blue-900 mb-2">Sources:</h4>
                <ul className="space-y-1 text-sm">
                  {ragResponse.sources.slice(0, 3).map((source, idx) => (
                    <li key={idx} className="text-gray-700">
                      • {source.headline}
                      <span className={`ml-2 badge badge-${source.sentiment?.toLowerCase()}`}>
                        {source.sentiment}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Key Metrics Table */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Key Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">Volatility (21d)</p>
            <p className="text-lg font-semibold">{stockData.volatility_21d?.toFixed(3)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Max Drawdown</p>
            <p className="text-lg font-semibold">{stockData.max_drawdown?.toFixed(2)}%</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Avg Sentiment</p>
            <p className="text-lg font-semibold">{stockData.avg_sentiment?.toFixed(3)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Liquidity Risk</p>
            <p className="text-lg font-semibold">{stockData.liquidity_risk?.toFixed(3)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDetails;
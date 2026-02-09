import { Link } from 'react-router-dom';

const RiskHeatmap = ({ data }) => {
  const getRiskColor = (score) => {
    if (score >= 0.8) return 'bg-red-600';
    if (score >= 0.6) return 'bg-orange-500';
    if (score >= 0.4) return 'bg-yellow-500';
    if (score >= 0.3) return 'bg-blue-500';
    return 'bg-green-500';
  };

  return (
    <div className="card">
      <h2 className="text-xl font-bold mb-4">Risk Heatmap</h2>
      <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
        {data.map((stock) => (
          <Link
            key={stock.symbol}
            to={`/stock/${stock.symbol}`}
            className={`
              ${getRiskColor(stock.risk_score)}
              text-white p-2 rounded text-center hover:opacity-80 transition-opacity
              flex flex-col justify-center items-center
            `}
            title={`${stock.symbol}: ${stock.risk_score?.toFixed(3)} (${stock.risk_level})`}
          >
            <div className="text-xs font-bold">{stock.symbol}</div>
            <div className="text-xs mt-1">{stock.risk_score?.toFixed(2)}</div>
          </Link>
        ))}
      </div>
      
      <div className="flex items-center justify-center space-x-4 mt-4 text-xs">
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>Low</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 bg-yellow-500 rounded"></div>
          <span>Medium</span>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-4 h-4 bg-red-600 rounded"></div>
          <span>High</span>
        </div>
      </div>
    </div>
  );
};

export default RiskHeatmap;
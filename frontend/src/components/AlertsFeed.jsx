import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

const AlertsFeed = ({ alerts }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Recent Alerts</h2>
        <p className="text-gray-500 text-center py-8">No active alerts</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Recent Alerts</h2>
        <Link to="/alerts" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          View All →
        </Link>
      </div>

      <div className="space-y-3">
        {alerts.map((alert, idx) => (
          <div
            key={idx}
            className="border-l-4 border-red-500 bg-red-50 p-3 rounded-r"
          >
            <div className="flex justify-between items-start mb-1">
              <Link
                to={`/stock/${alert.symbol}`}
                className="font-bold text-red-700 hover:text-red-900"
              >
                {alert.symbol}
              </Link>
              <span className="text-xs text-gray-500">
                {alert.timestamp && formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
              </span>
            </div>
            <p className="text-sm text-gray-700">{alert.alert_type?.replace('_', ' ')}</p>
            <p className="text-xs text-gray-600 mt-1">{alert.risk_drivers}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsFeed;
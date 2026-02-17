import React from 'react';
import { AlertTriangle, TrendingDown, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const AlertsList = ({ alerts }) => {
  const getAlertIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'high_risk':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'spike':
        return <TrendingDown className="w-5 h-5 text-orange-600" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return 'border-red-500 bg-red-50';
      case 'medium':
        return 'border-yellow-500 bg-yellow-50';
      default:
        return 'border-blue-500 bg-blue-50';
    }
  };

  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Recent Alerts
        </h2>
        <p className="text-gray-500 text-center py-8">No active alerts</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Recent Alerts
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Latest {alerts.length} risk notifications
        </p>
      </div>

      <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
        {alerts.map((alert, index) => (
          <div
            key={alert.id || index}
            className={`p-4 border-l-4 rounded-r-lg ${getSeverityColor(alert.severity)}`}
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-1">
                {getAlertIcon(alert.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-sm font-semibold text-gray-900">
                    {alert.symbol}
                  </h3>
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {alert.timestamp
                      ? formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })
                      : 'Just now'}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mb-2">
                  {alert.message || `${alert.type?.replace('_', ' ')} alert`}
                </p>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-gray-600">
                    Risk: <span className="font-semibold">{(alert.risk_score * 100).toFixed(1)}%</span>
                  </span>
                  {alert.severity && (
                    <span
                      className={`px-2 py-0.5 rounded font-semibold ${
                        alert.severity.toLowerCase() === 'high'
                          ? 'bg-red-200 text-red-800'
                          : alert.severity.toLowerCase() === 'medium'
                          ? 'bg-yellow-200 text-yellow-800'
                          : 'bg-blue-200 text-blue-800'
                      }`}
                    >
                      {alert.severity}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsList;
import React, { useEffect, useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

const LiveAlertToast = ({ alert, onClose }) => {
  const [show, setShow] = useState(true);

  useEffect(() => {
    // Auto-dismiss after 8 seconds
    const timer = setTimeout(() => {
      setShow(false);
      setTimeout(onClose, 300); // Wait for animation
    }, 8000);

    return () => clearTimeout(timer);
  }, [onClose]);

  if (!show) return null;

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return 'bg-red-500';
      case 'medium':
        return 'bg-yellow-500';
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-slide-up">
      <div className="bg-white rounded-lg shadow-2xl border-l-4 border-red-500 p-4 max-w-md">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${getSeverityColor(alert.severity)}`}>
            <AlertTriangle className="w-5 h-5 text-white" />
          </div>
          
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h4 className="font-semibold text-gray-900">
                New Alert: {alert.symbol}
              </h4>
              <button
                onClick={() => {
                  setShow(false);
                  setTimeout(onClose, 300);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            <p className="text-sm text-gray-600 mb-2">
              {alert.message || `${alert.type} alert detected`}
            </p>
            
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="font-medium">
                Risk Score: {(alert.risk_score * 100).toFixed(1)}%
              </span>
              <span>•</span>
              <span>{alert.type?.replace('_', ' ').toUpperCase()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveAlertToast;
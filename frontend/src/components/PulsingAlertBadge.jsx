// frontend/src/components/PulsingAlertBadge.jsx - FIXED
import React from 'react';
import { AlertCircle, Bell } from 'lucide-react';

const PulsingAlertBadge = ({ 
  count = 0, 
  severity = 'high', // 'high', 'medium', 'low'
  label = 'Alerts',
  onClick 
}) => {
  if (count === 0) return null;

  const severityConfig = {
    high: {
      bg: 'bg-red-500',
      text: 'text-red-600',
      ring: 'ring-red-400',
      icon: AlertCircle
    },
    medium: {
      bg: 'bg-yellow-500',
      text: 'text-yellow-600',
      ring: 'ring-yellow-400',
      icon: Bell
    },
    low: {
      bg: 'bg-blue-500',
      text: 'text-blue-600',
      ring: 'ring-blue-400',
      icon: Bell
    }
  };

  const config = severityConfig[severity] || severityConfig.high;
  const Icon = config.icon;

  return (
    <div 
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all hover:scale-105 relative ${
        onClick ? 'hover:shadow-lg' : ''
      }`}
    >
      {/* Pulsing Icon */}
      <div className="relative">
        <div className={`${config.bg} p-2 rounded-full`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        
        {/* Pulse Animation */}
        <div className={`absolute inset-0 ${config.bg} rounded-full animate-ping opacity-75`} />
        <div className={`absolute inset-0 ${config.bg} rounded-full animate-pulse`} />
      </div>

      {/* Count Badge */}
      <div className="flex flex-col">
        <span className="text-xs text-gray-500 font-medium">{label}</span>
        <span className={`text-2xl font-bold ${config.text} animate-pulse`}>
          {count}
        </span>
      </div>

      {/* Animated Ring */}
      <div className={`absolute inset-0 rounded-lg ${config.ring} ring-2 animate-ping-slow opacity-50`} />

      {/* REMOVED jsx ATTRIBUTE */}
      <style>{`
        @keyframes ping-slow {
          0%, 100% {
            transform: scale(1);
            opacity: 0.5;
          }
          50% {
            transform: scale(1.05);
            opacity: 0.3;
          }
        }

        .animate-ping-slow {
          animation: ping-slow 2s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
      `}</style>
    </div>
  );
};

export default PulsingAlertBadge;
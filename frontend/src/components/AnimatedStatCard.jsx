// frontend/src/components/AnimatedStatCard.jsx - FIXED
import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

const AnimatedStatCard = ({ 
  title, 
  value, 
  icon: Icon, 
  color = 'blue',
  trend,
  delay = 0 
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  // Animate number counting up
  useEffect(() => {
    if (value === displayValue) return;

    setIsAnimating(true);
    const duration = 1000; // 1 second
    const steps = 30;
    const stepValue = (value - displayValue) / steps;
    const stepDuration = duration / steps;

    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep++;
      if (currentStep === steps) {
        setDisplayValue(value);
        setIsAnimating(false);
        clearInterval(interval);
      } else {
        setDisplayValue(prev => Math.round(prev + stepValue));
      }
    }, stepDuration);

    return () => clearInterval(interval);
  }, [value]);

  const colorClasses = {
    blue: {
      bg: 'bg-blue-50',
      icon: 'bg-blue-500',
      text: 'text-blue-600',
      ring: 'ring-blue-200'
    },
    red: {
      bg: 'bg-red-50',
      icon: 'bg-red-500',
      text: 'text-red-600',
      ring: 'ring-red-200'
    },
    yellow: {
      bg: 'bg-yellow-50',
      icon: 'bg-yellow-500',
      text: 'text-yellow-600',
      ring: 'ring-yellow-200'
    },
    green: {
      bg: 'bg-green-50',
      icon: 'bg-green-500',
      text: 'text-green-600',
      ring: 'ring-green-200'
    }
  };

  const colors = colorClasses[color] || colorClasses.blue;

  return (
    <div 
      className={`${colors.bg} rounded-lg p-6 transition-all duration-500 hover:shadow-lg ${
        isAnimating ? `ring-4 ${colors.ring} scale-105` : ''
      }`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline gap-2 mt-2">
            <h3 
              className={`text-4xl font-bold ${colors.text} transition-all duration-300 ${
                isAnimating ? 'scale-110' : 'scale-100'
              }`}
            >
              {displayValue}
            </h3>
            
            {trend !== undefined && trend !== 0 && (
              <span className={`text-sm font-medium flex items-center ${
                trend > 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {trend > 0 ? (
                  <>
                    <TrendingUp className="w-4 h-4 mr-1" />
                    +{Math.abs(trend)}
                  </>
                ) : (
                  <>
                    <TrendingDown className="w-4 h-4 mr-1" />
                    -{Math.abs(trend)}
                  </>
                )}
              </span>
            )}
          </div>
        </div>
        
        <div className={`${colors.icon} p-3 rounded-full`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>

      {/* Animated Pulse Effect */}
      {isAnimating && (
        <div className="mt-2 overflow-hidden">
          <div className="h-1 bg-gradient-to-r from-transparent via-current to-transparent animate-shimmer" 
               style={{ 
                 width: '200%',
                 animation: 'shimmer 1s linear infinite'
               }}
          />
        </div>
      )}

      {/* REMOVED jsx ATTRIBUTE */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
};

export default AnimatedStatCard;
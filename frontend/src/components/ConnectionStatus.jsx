import React from 'react';

const ConnectionStatus = ({ isConnected }) => {
  return (
    <div className="fixed top-4 right-4 z-50">
      <div
        className={`flex items-center gap-2 px-3 py-2 rounded-lg shadow-lg ${
          isConnected
            ? 'bg-green-100 text-green-800 border border-green-300'
            : 'bg-red-100 text-red-800 border border-red-300'
        }`}
      >
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`}
        />
        <span className="text-sm font-medium">
          {isConnected ? 'Live' : 'Disconnected'}
        </span>
      </div>
    </div>
  );
};

export default ConnectionStatus;
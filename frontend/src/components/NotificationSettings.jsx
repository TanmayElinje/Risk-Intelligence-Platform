// frontend/src/components/NotificationSettings.jsx
import React from 'react';
import { Bell, BellOff, Volume2, VolumeX } from 'lucide-react';
import { useNotifications } from '../hooks/useNotifications';

const NotificationSettings = () => {
  const {
    permission,
    soundEnabled,
    requestPermission,
    toggleSound,
    showNotification,
  } = useNotifications();

  const handleTestNotification = () => {
    showNotification('Test Notification', {
      body: 'This is a test notification from Risk Intelligence Platform',
      soundType: 'alert',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Bell className="w-5 h-5" />
        Notification Settings
      </h3>

      <div className="space-y-4">
        {/* Browser Notifications */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            {permission === 'granted' ? (
              <Bell className="w-5 h-5 text-green-600" />
            ) : (
              <BellOff className="w-5 h-5 text-gray-400" />
            )}
            <div>
              <p className="font-medium text-gray-900">Browser Notifications</p>
              <p className="text-sm text-gray-500">
                {permission === 'granted'
                  ? 'Enabled'
                  : permission === 'denied'
                  ? 'Blocked (reset in browser settings)'
                  : 'Not enabled'}
              </p>
            </div>
          </div>
          {permission !== 'granted' && permission !== 'denied' && (
            <button
              onClick={requestPermission}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              Enable
            </button>
          )}
        </div>

        {/* Sound Alerts */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            {soundEnabled ? (
              <Volume2 className="w-5 h-5 text-blue-600" />
            ) : (
              <VolumeX className="w-5 h-5 text-gray-400" />
            )}
            <div>
              <p className="font-medium text-gray-900">Sound Alerts</p>
              <p className="text-sm text-gray-500">
                {soundEnabled ? 'Enabled' : 'Disabled'}
              </p>
            </div>
          </div>
          <button
            onClick={toggleSound}
            className={`px-4 py-2 rounded-lg transition-colors text-sm ${
              soundEnabled
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {soundEnabled ? 'Disable' : 'Enable'}
          </button>
        </div>

        {/* Test Button */}
        <button
          onClick={handleTestNotification}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
        >
          Test Notification
        </button>
      </div>

      {/* Info */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-xs text-blue-800">
          💡 You'll receive notifications for high-risk alerts and significant risk changes
        </p>
      </div>
    </div>
  );
};

export default NotificationSettings;
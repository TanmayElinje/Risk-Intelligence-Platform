// frontend/src/pages/Settings.jsx
import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Bell, Eye, Mail, Send, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import NotificationSettings from '../components/NotificationSettings';
import { getToken } from '../services/authService';

// ==================== TOGGLE SWITCH ====================
const Toggle = ({ checked, onChange, disabled = false }) => (
  <label className={`relative inline-flex items-center ${disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}>
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      disabled={disabled}
      className="sr-only peer"
    />
    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
  </label>
);

// ==================== EMAIL ALERTS SECTION ====================
const EmailAlertSettings = () => {
  const [prefs, setPrefs] = useState({
    email_alerts_enabled: false,
    alert_email: '',
    high_risk_alerts: true,
    medium_risk_alerts: false,
    daily_digest: false,
    watchlist_only: false,
  });
  const [smtpStatus, setSmtpStatus] = useState({ configured: false, smtp_user: null });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [sendingDigest, setSendingDigest] = useState(false);
  const [message, setMessage] = useState(null); // { type: 'success'|'error', text: '' }

  const token = getToken();
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // Load preferences and SMTP status
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [prefsRes, statusRes] = await Promise.all([
          fetch('http://localhost:5000/api/email/preferences', { headers }),
          fetch('http://localhost:5000/api/email/status', { headers }),
        ]);
        const prefsData = await prefsRes.json();
        const statusData = await statusRes.json();

        if (prefsData.preferences) setPrefs(prefsData.preferences);
        setSmtpStatus(statusData);
      } catch (err) {
        console.error('Error loading email settings:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Save preferences
  const savePrefs = async (updatedPrefs) => {
    setMessage(null);
    setSaving(true);
    try {
      const res = await fetch('http://localhost:5000/api/email/preferences', {
        method: 'PUT',
        headers,
        body: JSON.stringify(updatedPrefs),
      });
      const data = await res.json();
      if (res.ok) {
        setPrefs(data.preferences);
        setMessage({ type: 'success', text: 'Preferences saved' });
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to save' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error' });
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const updatePref = (key, value) => {
    const updated = { ...prefs, [key]: value };
    setPrefs(updated);
    savePrefs(updated);
  };

  // Send test email
  const sendTestEmail = async () => {
    setMessage(null);
    setTesting(true);
    try {
      const res = await fetch('http://localhost:5000/api/email/test', {
        method: 'POST',
        headers,
        body: JSON.stringify({ email: prefs.alert_email }),
      });
      const data = await res.json();
      setMessage({
        type: data.success ? 'success' : 'error',
        text: data.message,
      });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to send test email' });
    } finally {
      setTesting(false);
    }
  };

  // Send daily digest
  const sendDigest = async () => {
    setMessage(null);
    setSendingDigest(true);
    try {
      const res = await fetch('http://localhost:5000/api/email/digest', {
        method: 'POST',
        headers,
      });
      const data = await res.json();
      setMessage({
        type: data.success ? 'success' : 'error',
        text: data.message,
      });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to send digest' });
    } finally {
      setSendingDigest(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 transition-colors">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span className="text-gray-500 text-sm">Loading email settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 transition-colors lg:col-span-2">
      <h3 className="text-lg font-semibold mb-1 flex items-center gap-2 text-gray-900">
        <Mail className="w-5 h-5" />
        Email Alerts
      </h3>
      <p className="text-sm text-gray-500 mb-5">
        Receive risk alerts and daily digests via email
      </p>

      {/* SMTP Status Banner */}
      {!smtpStatus.configured && (
        <div className="mb-5 px-4 py-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800 font-medium">SMTP not configured</p>
          <p className="text-xs text-yellow-700 mt-1">
            Add <code className="bg-yellow-100 px-1 rounded">SMTP_USER</code> and <code className="bg-yellow-100 px-1 rounded">SMTP_PASSWORD</code> to your <code className="bg-yellow-100 px-1 rounded">.env</code> file. For Gmail, use an App Password.
          </p>
        </div>
      )}

      {smtpStatus.configured && (
        <div className="mb-5 px-4 py-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
          <p className="text-sm text-green-800">
            SMTP configured — sending from <strong>{smtpStatus.smtp_user}</strong>
          </p>
        </div>
      )}

      {/* Feedback Message */}
      {message && (
        <div className={`mb-5 px-4 py-3 rounded-lg flex items-center gap-2 text-sm ${
          message.type === 'success'
            ? 'bg-green-50 border border-green-200 text-green-800'
            : 'bg-red-50 border border-red-200 text-red-800'
        }`}>
          {message.type === 'success'
            ? <CheckCircle className="w-4 h-4 flex-shrink-0" />
            : <AlertCircle className="w-4 h-4 flex-shrink-0" />
          }
          {message.text}
        </div>
      )}

      <div className="space-y-4">
        {/* Master Toggle */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900">Enable Email Alerts</p>
            <p className="text-sm text-gray-500">Turn on/off all email notifications</p>
          </div>
          <Toggle
            checked={prefs.email_alerts_enabled}
            onChange={(val) => updatePref('email_alerts_enabled', val)}
          />
        </div>

        {/* Email Address */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Alert Email Address
          </label>
          <div className="flex gap-2">
            <input
              type="email"
              value={prefs.alert_email || ''}
              onChange={(e) => setPrefs({ ...prefs, alert_email: e.target.value })}
              onBlur={() => savePrefs(prefs)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
              placeholder="your@email.com"
            />
            <button
              onClick={sendTestEmail}
              disabled={testing || !smtpStatus.configured || !prefs.alert_email}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-sm rounded-lg font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap"
            >
              {testing ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Sending...</>
              ) : (
                <><Send className="w-4 h-4" /> Test</>
              )}
            </button>
          </div>
        </div>

        {/* Alert Type Toggles */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900">High Risk Alerts</p>
            <p className="text-sm text-gray-500">Email when a stock crosses high risk threshold</p>
          </div>
          <Toggle
            checked={prefs.high_risk_alerts}
            onChange={(val) => updatePref('high_risk_alerts', val)}
            disabled={!prefs.email_alerts_enabled}
          />
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900">Medium Risk Alerts</p>
            <p className="text-sm text-gray-500">Email when a stock crosses medium risk threshold</p>
          </div>
          <Toggle
            checked={prefs.medium_risk_alerts}
            onChange={(val) => updatePref('medium_risk_alerts', val)}
            disabled={!prefs.email_alerts_enabled}
          />
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900">Watchlist Only</p>
            <p className="text-sm text-gray-500">Only send alerts for your watchlist stocks</p>
          </div>
          <Toggle
            checked={prefs.watchlist_only}
            onChange={(val) => updatePref('watchlist_only', val)}
            disabled={!prefs.email_alerts_enabled}
          />
        </div>

        {/* Daily Digest */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div>
            <p className="font-medium text-gray-900">Daily Digest</p>
            <p className="text-sm text-gray-500">Receive a daily summary of all risk levels</p>
          </div>
          <div className="flex items-center gap-3">
            <Toggle
              checked={prefs.daily_digest}
              onChange={(val) => updatePref('daily_digest', val)}
              disabled={!prefs.email_alerts_enabled}
            />
            <button
              onClick={sendDigest}
              disabled={sendingDigest || !smtpStatus.configured || !prefs.alert_email}
              className="px-3 py-1.5 text-xs bg-gray-200 hover:bg-gray-300 disabled:opacity-50 text-gray-700 rounded-md font-medium transition-colors flex items-center gap-1"
            >
              {sendingDigest ? (
                <><Loader2 className="w-3 h-3 animate-spin" /> Sending...</>
              ) : (
                'Send Now'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};


// ==================== MAIN SETTINGS PAGE ====================
const Settings = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <SettingsIcon className="w-8 h-8" />
          Settings
        </h1>
        <p className="text-gray-600 mt-2">
          Customize your Risk Intelligence Platform experience
        </p>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Notification Settings */}
        <NotificationSettings />

        {/* Alert Preferences */}
        <div className="bg-white rounded-lg shadow p-6 transition-colors">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-900">
            <Bell className="w-5 h-5" />
            Alert Preferences
          </h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">High Risk Alerts</p>
                <p className="text-sm text-gray-500">Notify when risk score exceeds 60%</p>
              </div>
              <Toggle checked={true} onChange={() => {}} />
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Medium Risk Alerts</p>
                <p className="text-sm text-gray-500">Notify when risk score exceeds 40%</p>
              </div>
              <Toggle checked={true} onChange={() => {}} />
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Watchlist Alerts</p>
                <p className="text-sm text-gray-500">Notify for stocks in your watchlist</p>
              </div>
              <Toggle checked={true} onChange={() => {}} />
            </div>
          </div>
        </div>

        {/* Email Alerts - Full Width */}
        <EmailAlertSettings />

        {/* Display Preferences */}
        <div className="bg-white rounded-lg shadow p-6 transition-colors">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-900">
            <Eye className="w-5 h-5" />
            Display Preferences
          </h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Show Ticker</p>
                <p className="text-sm text-gray-500">Display live risk ticker at top</p>
              </div>
              <Toggle checked={true} onChange={() => {}} />
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Compact View</p>
                <p className="text-sm text-gray-500">Show more data in less space</p>
              </div>
              <Toggle checked={false} onChange={() => {}} />
            </div>
          </div>
        </div>

        {/* Account Info */}
        <div className="bg-white rounded-lg shadow p-6 transition-colors">
          <h3 className="text-lg font-semibold mb-4 text-gray-900">Account Information</h3>
          
          <div className="space-y-3">
            <div>
              <label className="text-sm text-gray-600">Plan</label>
              <p className="font-medium text-gray-900">Free Tier</p>
            </div>
            
            <div>
              <label className="text-sm text-gray-600">Member Since</label>
              <p className="font-medium text-gray-900">
                {new Date().toLocaleDateString('en-US', { 
                  month: 'long', 
                  year: 'numeric' 
                })}
              </p>
            </div>
          </div>

          <button className="w-full mt-6 px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-sm font-medium">
            Upgrade to Pro
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
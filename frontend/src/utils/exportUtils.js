// frontend/src/utils/exportUtils.js
/**
 * Utility functions for exporting data to CSV and Excel formats
 */

/**
 * Convert array of objects to CSV string
 */
export const convertToCSV = (data, columns) => {
  if (!data || data.length === 0) return '';

  // Create header row
  const headers = columns || Object.keys(data[0]);
  const headerRow = headers.join(',');

  // Create data rows
  const dataRows = data.map(item => {
    return headers.map(header => {
      const value = item[header];
      // Handle values with commas or quotes
      if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value ?? '';
    }).join(',');
  });

  return [headerRow, ...dataRows].join('\n');
};

/**
 * Download data as CSV file
 */
export const downloadCSV = (data, filename = 'data.csv', columns = null) => {
  const csv = convertToCSV(data, columns);
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Download data as JSON file
 */
export const downloadJSON = (data, filename = 'data.json') => {
  const jsonStr = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

/**
 * Format risk scores data for export
 */
export const formatRiskScoresForExport = (scores) => {
  return scores.map(stock => ({
    Symbol: stock.symbol,
    'Risk Score': `${(stock.risk_score * 100).toFixed(2)}%`,
    'Risk Level': stock.risk_level,
    Sentiment: stock.avg_sentiment > 0 ? 'Positive' : stock.avg_sentiment < 0 ? 'Negative' : 'Neutral',
    'Sentiment Score': stock.avg_sentiment?.toFixed(2) || 'N/A',
    Date: new Date().toLocaleDateString(),
  }));
};

/**
 * Format watchlist data for export
 */
export const formatWatchlistForExport = (watchlist) => {
  return watchlist.map(item => ({
    Symbol: item.symbol,
    Name: item.name,
    Sector: item.sector,
    'Risk Score': item.risk_score ? `${(item.risk_score * 100).toFixed(2)}%` : 'N/A',
    'Risk Level': item.risk_level || 'N/A',
    Notes: item.notes || '',
    'Added Date': item.added_at ? new Date(item.added_at).toLocaleDateString() : 'N/A',
  }));
};

/**
 * Format alerts data for export
 */
export const formatAlertsForExport = (alerts) => {
  return alerts.map(alert => ({
    Symbol: alert.symbol,
    'Alert Type': alert.alert_type,
    'Risk Score': alert.risk_score ? `${alert.risk_score}%` : 'N/A',
    'Risk Level': alert.risk_level,
    Message: alert.message || alert.alert_type,
    Date: alert.created_at ? new Date(alert.created_at).toLocaleDateString() : 'N/A',
  }));
};
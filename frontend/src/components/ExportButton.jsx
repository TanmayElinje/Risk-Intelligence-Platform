// frontend/src/components/ExportButton.jsx
import React, { useState } from 'react';
import { Download, FileText, FileSpreadsheet } from 'lucide-react';

const ExportButton = ({ 
  data, 
  filename = 'export',
  formatData = (d) => d,
  label = 'Export'
}) => {
  const [showMenu, setShowMenu] = useState(false);

  const handleExportCSV = () => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    const formattedData = formatData(data);
    const headers = Object.keys(formattedData[0]);
    
    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...formattedData.map(row => 
        headers.map(header => {
          const value = row[header];
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? '';
        }).join(',')
      )
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setShowMenu(false);
  };

  const handleExportJSON = () => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    const formattedData = formatData(data);
    const jsonStr = JSON.stringify(formattedData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setShowMenu(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
      >
        <Download className="w-4 h-4" />
        {label}
      </button>

      {showMenu && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setShowMenu(false)}
          />
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-20 border border-gray-200">
            <button
              onClick={handleExportCSV}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
            >
              <FileSpreadsheet className="w-4 h-4" />
              Export as CSV
            </button>
            
            <button
              onClick={handleExportJSON}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Export as JSON
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default ExportButton;
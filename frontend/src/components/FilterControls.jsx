// frontend/src/components/FilterControls.jsx
import React from 'react';
import { Search, SlidersHorizontal, X } from 'lucide-react';

const FilterControls = ({ 
  searchTerm, 
  setSearchTerm,
  riskFilter,
  setRiskFilter,
  sortBy,
  setSortBy,
  showFilters,
  setShowFilters
}) => {
  const clearFilters = () => {
    setSearchTerm('');
    setRiskFilter('all');
    setSortBy('risk_desc');
  };

  const hasActiveFilters = searchTerm || riskFilter !== 'all' || sortBy !== 'risk_desc';

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search stocks by symbol..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            showFilters 
              ? 'bg-blue-100 text-blue-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
          {hasActiveFilters && (
            <span className="w-2 h-2 bg-blue-600 rounded-full"></span>
          )}
        </button>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Risk Level Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Risk Level
              </label>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Risk Levels</option>
                <option value="high">High Risk Only</option>
                <option value="medium">Medium Risk Only</option>
                <option value="low">Low Risk Only</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="risk_desc">Risk Score (High to Low)</option>
                <option value="risk_asc">Risk Score (Low to High)</option>
                <option value="symbol_asc">Symbol (A-Z)</option>
                <option value="symbol_desc">Symbol (Z-A)</option>
                <option value="sentiment_desc">Sentiment (Positive First)</option>
                <option value="sentiment_asc">Sentiment (Negative First)</option>
              </select>
            </div>
          </div>

          {/* Active Filters Summary */}
          {hasActiveFilters && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-gray-600">Active filters:</span>
                
                {searchTerm && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full flex items-center gap-1">
                    Search: "{searchTerm}"
                    <button onClick={() => setSearchTerm('')} className="hover:text-blue-900">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}
                
                {riskFilter !== 'all' && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full flex items-center gap-1">
                    Risk: {riskFilter}
                    <button onClick={() => setRiskFilter('all')} className="hover:text-blue-900">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}
                
                {sortBy !== 'risk_desc' && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                    Sorted
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FilterControls;
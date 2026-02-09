import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const SearchBar = ({ stocks }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const navigate = useNavigate();

  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value);

    if (value.length > 0) {
      const filtered = stocks.filter(stock =>
        stock.symbol.toLowerCase().includes(value.toLowerCase())
      ).slice(0, 5);
      setSuggestions(filtered);
    } else {
      setSuggestions([]);
    }
  };

  const handleSelect = (symbol) => {
    navigate(`/stock/${symbol}`);
    setQuery('');
    setSuggestions([]);
  };

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={handleSearch}
        placeholder="Search stocks... (e.g., AAPL, MSFT)"
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
      
      {suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
          {suggestions.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => handleSelect(stock.symbol)}
              className="w-full px-4 py-2 text-left hover:bg-gray-50 flex justify-between items-center"
            >
              <span className="font-medium">{stock.symbol}</span>
              <span className={`badge badge-${stock.risk_level?.toLowerCase()}`}>
                {stock.risk_level}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
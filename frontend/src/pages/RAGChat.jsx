import { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

const RAGChat = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hi! I'm your AI financial risk analyst. Ask me anything about stocks, risk factors, or market sentiment. For example:\n\n• Why is AAPL's risk high?\n• What's causing volatility in tech stocks?\n• Summarize latest news for MSFT\n• Which stocks have negative sentiment?",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
  e.preventDefault();
  if (!input.trim() || loading) return;

  const userMessage = {
    role: 'user',
    content: input,
    timestamp: new Date(),
  };

  setMessages(prev => [...prev, userMessage]);
  setInput('');
  setLoading(true);

  try {
    // Detect if query mentions a specific stock symbol
    const stockMatch = input.match(/\b([A-Z]{2,5})\b/);
    const stockSymbol = stockMatch ? stockMatch[1] : null;

    console.log('Sending query:', input, 'Stock:', stockSymbol); // Debug log

    const response = await apiService.queryRAG(input, stockSymbol);
    
    console.log('Received response:', response.data); // Debug log

    // Handle response data
    const responseData = response.data;
    
    const assistantMessage = {
      role: 'assistant',
      content: responseData.explanation || "I couldn't generate a response. Please try again.",
      sources: responseData.sources || [],
      confidence: responseData.confidence || 0,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, assistantMessage]);
    
    // Show success toast
    toast.success('Response generated!');
    
  } catch (error) {
    console.error('Chat error:', error);
    console.error('Error details:', error.response?.data); // Debug log
    
    // Try to extract error message from response
    let errorContent = "I'm sorry, I encountered an error processing your question.";
    
    if (error.response?.data?.explanation) {
      errorContent = error.response.data.explanation;
    } else if (error.response?.data?.error) {
      errorContent = error.response.data.error;
    }
    
    const errorMessage = {
      role: 'assistant',
      content: errorContent + " Please try again or rephrase your question.",
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, errorMessage]);
    toast.error('Failed to get response');
  } finally {
    setLoading(false);
  }
};

  const suggestedQuestions = [
    "What are the top 5 highest risk stocks?",
    "Why is COIN considered high risk?",
    "Which stocks have the most negative sentiment?",
    "What's driving volatility in tech stocks?",
    "Summarize recent market trends",
  ];

  const handleSuggestionClick = (question) => {
    setInput(question);
  };

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-3xl font-bold">🤖 AI Assistant</h1>
        <p className="text-gray-600 mt-1">Ask questions about stocks, risk, and market sentiment</p>
      </div>

      {/* Chat Container */}
      <div className="flex-1 card overflow-hidden flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-start space-x-2">
                  <div className="text-2xl">
                    {message.role === 'user' ? '👤' : '🤖'}
                  </div>
                  <div className="flex-1">
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-300">
                        <p className="text-sm font-semibold mb-2">📚 Sources:</p>
                        <ul className="space-y-1 text-sm">
                          {message.sources.slice(0, 3).map((source, sidx) => (
                            <li key={sidx} className="flex items-start space-x-2">
                              <span>•</span>
                              <div>
                                <span>{source.headline}</span>
                                {source.sentiment && (
                                  <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
                                    source.sentiment === 'positive' ? 'bg-green-200 text-green-800' :
                                    source.sentiment === 'negative' ? 'bg-red-200 text-red-800' :
                                    'bg-gray-200 text-gray-800'
                                  }`}>
                                    {source.sentiment}
                                  </span>
                                )}
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <p className="text-xs mt-2 opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-4 max-w-3xl">
                <div className="flex items-center space-x-2">
                  <div className="text-2xl">🤖</div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Questions */}
        {messages.length === 1 && (
          <div className="px-4 pb-4">
            <p className="text-sm font-medium text-gray-700 mb-2">💡 Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestionClick(question)}
                  className="text-sm px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about stocks or risk..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RAGChat;
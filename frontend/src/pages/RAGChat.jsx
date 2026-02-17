import { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import { Send, ExternalLink, Bot, User, Sparkles } from 'lucide-react';

const RAGChat = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm your AI financial assistant. I can help you with:\n\n• Any finance question — mutual funds, Sharpe ratio, options, SIP calculations, etc.\n• Stock-specific analysis — risk scores, news, sentiment for stocks in your portfolio\n• Portfolio insights — highest/lowest risk stocks, risk summaries\n\nAsk me anything about finance!",
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

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
      const stockMatch = input.match(/\b([A-Z]{2,5})\b/);
      const stockSymbol = stockMatch ? stockMatch[1] : null;

      // Build chat history from last 10 messages (5 turns)
      const history = [...messages, userMessage]
        .filter(m => m.content)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }));

      // Add placeholder assistant message for streaming
      const assistantIdx = messages.length + 1; // index after user message
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '',
        sources: [],
        timestamp: new Date(),
        streaming: true,
      }]);

      // Use SSE streaming endpoint
      const res = await fetch('http://localhost:5000/api/query-rag-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, stock_symbol: stockSymbol, chat_history: history }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamedText = '';
      let streamSources = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));

            if (event.type === 'meta') {
              streamSources = event.sources || [];
            } else if (event.type === 'token') {
              streamedText += event.content;
              // Don't display the FOLLOW_UP line while streaming
              const displayText = streamedText.split('FOLLOW_UP:')[0].trim();
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: displayText,
                  sources: streamSources,
                };
                return updated;
              });
            } else if (event.type === 'done') {
              // Strip FOLLOW_UP line from displayed text
              const cleanText = streamedText.split('FOLLOW_UP:')[0].trim();
              const followUps = event.follow_ups || [];
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: cleanText,
                  sources: streamSources,
                  followUps: followUps,
                  streaming: false,
                };
                return updated;
              });
            } else if (event.type === 'error') {
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: event.content || 'An error occurred.',
                  streaming: false,
                };
                return updated;
              });
            }
          } catch (e) { /* skip malformed events */ }
        }
      }

    } catch (error) {
      console.error('Chat error:', error);

      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        // If last message is the streaming placeholder, update it
        if (last && last.role === 'assistant' && last.streaming) {
          updated[updated.length - 1] = {
            ...last,
            content: "I'm sorry, I encountered an error. Please try again.",
            streaming: false,
          };
        } else {
          updated.push({
            role: 'assistant',
            content: "I'm sorry, I encountered an error. Please try again.",
            timestamp: new Date(),
          });
        }
        return updated;
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSuggestionClick = (question) => {
    setInput(question);
    inputRef.current?.focus();
  };

  const suggestedQuestions = [
    { label: "Top risk stocks", query: "What are the highest risk stocks in my portfolio?" },
    { label: "Explain Sharpe ratio", query: "What is the Sharpe ratio and how is it calculated?" },
    { label: "NVDA analysis", query: "Give me a risk analysis for NVDA" },
    { label: "Latest market news", query: "Summarize the latest news for AAPL" },
    { label: "SIP calculator", query: "If I invest 10000 per month in a mutual fund with 12% annual returns, what will be my corpus after 15 years?" },
    { label: "Portfolio summary", query: "Give me a risk summary of my entire portfolio" },
  ];

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Bot className="w-8 h-8 text-blue-600" />
          AI Financial Assistant
        </h1>
        <p className="text-gray-600 mt-1">Ask any finance question — stocks, risk, markets, investments, calculations</p>
      </div>

      {/* Chat Container */}
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-2xl p-4 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-50 text-gray-900 border border-gray-200'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user' ? 'bg-blue-700' : 'bg-blue-100'
                  }`}>
                    {message.role === 'user' 
                      ? <User className="w-4 h-4 text-white" />
                      : <Bot className="w-4 h-4 text-blue-600" />
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                    
                    {/* Sources with clickable links */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-sm font-semibold mb-2 text-gray-700">📚 Sources:</p>
                        <div className="space-y-2">
                          {message.sources.slice(0, 5).map((source, sidx) => (
                            <div key={sidx} className="flex items-start gap-2 text-sm bg-white rounded-lg p-2 border border-gray-100">
                              <span className="text-gray-400 mt-0.5">{sidx + 1}.</span>
                              <div className="flex-1 min-w-0">
                                {/* Headline or source name */}
                                <p className="font-medium text-gray-800 truncate">
                                  {source.headline || source.source || 'News Article'}
                                </p>
                                
                                {/* Publisher + sentiment */}
                                <div className="flex items-center gap-2 mt-1">
                                  {source.source && source.source !== source.headline && (
                                    <span className="text-xs text-gray-500">{source.source}</span>
                                  )}
                                  {source.sentiment && (
                                    <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                                      source.sentiment === 'positive' ? 'bg-green-100 text-green-700' :
                                      source.sentiment === 'negative' ? 'bg-red-100 text-red-700' :
                                      'bg-gray-100 text-gray-600'
                                    }`}>
                                      {source.sentiment}
                                    </span>
                                  )}
                                </div>

                                {/* Clickable article link */}
                                {source.url && (
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 hover:underline mt-1"
                                  >
                                    <ExternalLink className="w-3 h-3" />
                                    Read full article
                                  </a>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Follow-up suggestions */}
                    {message.followUps && message.followUps.length > 0 && !message.streaming && (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-xs font-medium text-gray-500 mb-2">💡 Follow-up questions:</p>
                        <div className="flex flex-wrap gap-2">
                          {message.followUps.map((q, fidx) => (
                            <button
                              key={fidx}
                              onClick={() => handleSuggestionClick(q)}
                              className="text-xs px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors border border-blue-100"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-50 border border-gray-200 rounded-2xl p-4 max-w-3xl">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm text-gray-500">Thinking...</span>
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
            <div className="flex items-center gap-1 mb-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <p className="text-sm font-medium text-gray-600">Try asking:</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((sq, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestionClick(sq.query)}
                  className="text-sm px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors border border-blue-100"
                >
                  {sq.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about finance, stocks, or your portfolio..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              <span className="hidden sm:inline">Send</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RAGChat;
# Financial Risk Intelligence Platform

AI-powered multi-agent system for real-time financial risk monitoring, combining market data from Yahoo Finance, FinBERT news sentiment analysis, explainable RAG-based insights, and an interactive React dashboard.

## Features

### Core Platform
- **Multi-Agent Architecture** — 5 specialized agents (Market Data, Sentiment, RAG, Risk Scoring, Alert) working together to assess stock risk
- **Real-Time Risk Monitoring** — Track 50 US tech stocks with composite risk scores updated from live Yahoo Finance data
- **News Sentiment Analysis** — FinBERT-powered sentiment scoring on 400+ real news articles scraped from Yahoo Finance with full article content extraction
- **Explainable AI** — RAG-based explanations using FAISS vector search + Ollama LLM (llama3) to explain why stocks are flagged as high risk
- **AI Financial Assistant** — Chatbot that answers any finance question, with access to portfolio risk data and real news when relevant. Includes domain guardrails
- **PostgreSQL Database** — Full relational database with stocks, market data, risk scores, news, sentiment, alerts, portfolio, and watchlist tables

### Dashboard & Analytics
- **Interactive Dashboard** — Real-time risk overview with stats cards, risk score table, live ticker, and alert feed
- **Portfolio Management** — Add/remove holdings, track portfolio-level risk metrics
- **Watchlist** — Save and monitor stocks of interest
- **Stock Comparison** — Side-by-side comparison of multiple stocks across risk metrics
- **Historical Data** — Interactive price charts with technical indicators
- **Advanced Analytics** — Correlation matrix, Monte Carlo simulation, Value at Risk (VaR), and portfolio optimization (Markowitz efficient frontier)
- **Backtesting Engine** — Test 4 strategies (Buy & Hold, Moving Average Crossover, Risk-Based, Mean Reversion) against historical data with equity curves, trade logs, and performance metrics (Sharpe, Sortino, max drawdown, win rate)
- **Email Alerts** — Configurable email digest for risk alerts (daily/weekly/threshold-based)
- **Data Export** — Export risk data to CSV/JSON with filtering

### Data Pipeline
- **Real Market Data** — `yf.download()` bulk fetching for 50 stocks (1 year of OHLCV data)
- **Real News** — `yf.Search()` per-stock news + BeautifulSoup full article scraping
- **FinBERT Sentiment** — Enhanced analysis: headline (40%) + full content (60%) weighted scoring
- **Risk Scoring** — Composite score from volatility (40%), drawdown (30%), sentiment (20%), liquidity (10%)
- **RAG Knowledge Base** — FAISS vector store built from 400+ real articles for contextual explanations

## Architecture

```
Yahoo Finance API ──→ Market Data Agent ──→ Risk Features
                                              ↓
Yahoo Finance News ──→ News Fetcher ──→ FinBERT Sentiment Agent
                                              ↓
                                      Risk Scoring Agent ──→ Risk Scores
                                              ↓
FAISS Vector DB ←── RAG Agent ←── Alert Agent ──→ Alerts + Explanations
                                              ↓
PostgreSQL ←──────────────────────────→ Flask API ──→ React Dashboard
```

### Agents
1. **MarketDataAgent** — Computes volatility (21d/60d), max drawdown, beta, Sharpe ratio, liquidity risk, returns
2. **SentimentAgent** — FinBERT-based sentiment analysis with enhanced headline + content weighting
3. **NewsRAGAgent** — FAISS vector store + Ollama LLM for generating contextual explanations
4. **RiskScoringAgent** — Normalizes and combines features into a 0-1 composite risk score with risk level classification (High/Medium/Low)
5. **AlertAgent** — Detects high-risk stocks and sudden risk spikes, generates RAG-powered explanations

## Tech Stack

**Backend:** Python 3.11+, Flask, SQLAlchemy, PostgreSQL, Pandas, NumPy, yfinance, BeautifulSoup, FinBERT (transformers + PyTorch), LangChain, FAISS, Ollama/llama3, Flask-SocketIO

**Frontend:** React 18, Vite, TailwindCSS, Recharts, Lucide React, React Router

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Ollama with llama3 model — [Install Ollama](https://ollama.ai)

## Installation

### 1. Clone & Setup Backend

```bash
git clone https://github.com/yourusername/risk-intelligence-platform.git
cd risk-intelligence-platform

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your PostgreSQL credentials:
```
DATABASE_URL=postgresql://username:password@localhost:5432/risk_intelligence
SECRET_KEY=your-secret-key
```

### 3. Setup Database

```bash
# Create the PostgreSQL database, then:
python -m backend.database.init_db
```

### 4. Install Ollama & Pull Model

```bash
ollama pull llama3
```

### 5. Setup Frontend

```bash
cd frontend
npm install
```

## Usage

### Populate Real Data

```bash
# Fetch real stock data + news + sentiment + risk scores (full pipeline)
python -m backend.scripts.refresh_real_data

# Options:
#   --period 3mo          Shorter data range (default: 1y)
#   --symbols AAPL,MSFT   Specific stocks only
#   --skip-news           Skip news fetching
#   --skip-risk           Skip risk recomputation
#   --skip-alerts         Skip alert generation
#   --with-metadata       Also fetch stock names/sectors from Yahoo

# Rebuild RAG vector store (after news refresh)
python -m backend.scripts.rebuild_rag
```

### Run the Platform

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Flask API
python -m backend.api.app

# Terminal 3: Start React frontend
cd frontend
npm run dev
```

Access the dashboard at: `http://localhost:5173`

### Run Full Pipeline

```bash
# Runs all steps: data verification, market features, sentiment, RAG, risk scores, alerts
python -m backend.main
```

## Project Structure

```
risk-intelligence-platform/
├── backend/
│   ├── agents/                # Multi-agent system
│   │   ├── market_agent.py    # Market feature computation
│   │   ├── sentiment_agent.py # FinBERT sentiment analysis
│   │   ├── rag_agent.py       # RAG explanations (FAISS + LLM)
│   │   ├── risk_agent.py      # Composite risk scoring
│   │   └── alert_agent.py     # Alert detection + notifications
│   ├── api/
│   │   ├── app.py             # Flask application factory
│   │   ├── routes.py          # API endpoints + AI assistant
│   │   ├── auth_routes.py     # Authentication (JWT)
│   │   ├── email_routes.py    # Email alert configuration
│   │   ├── backtest_routes.py # Backtesting engine API
│   │   └── portfolio_routes.py# Portfolio & watchlist API
│   ├── configs/
│   │   └── config.yaml        # Agent params, stock list, weights
│   ├── database/
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── db_service.py      # Database service layer
│   │   └── init_db.py         # DB initialization & seeding
│   ├── scrapers/
│   │   ├── yfinance_collector.py  # Stock data (yf.download)
│   │   ├── news_fetcher.py        # News (yf.Search + scraping)
│   │   └── selenium_news_scraper.py # Alternative Selenium scraper
│   ├── scripts/
│   │   ├── refresh_real_data.py   # Full data refresh pipeline
│   │   └── rebuild_rag.py        # Rebuild FAISS vector store
│   ├── data/
│   │   ├── raw/               # Raw parquet files
│   │   ├── processed/         # Processed CSVs
│   │   └── vector_db/         # FAISS index
│   ├── websocket/             # Real-time WebSocket server
│   └── main.py                # Pipeline orchestrator
├── frontend/
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   │   ├── Layout.jsx     # Main layout with nav dropdown
│   │   │   ├── LiveRiskTicker.jsx  # Scrolling risk ticker
│   │   │   ├── RiskScoreTable.jsx  # Sortable risk table
│   │   │   └── ...
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx       # Main dashboard
│   │   │   ├── Portfolio.jsx       # Portfolio management
│   │   │   ├── Watchlist.jsx       # Stock watchlist
│   │   │   ├── StockComparison.jsx # Side-by-side comparison
│   │   │   ├── HistoricalData.jsx  # Price charts
│   │   │   ├── AdvancedAnalytics.jsx # Correlation, Monte Carlo, VaR
│   │   │   ├── Backtesting.jsx     # Strategy backtesting
│   │   │   ├── RAGChat.jsx         # AI assistant chat
│   │   │   ├── Alerts.jsx          # Alert management
│   │   │   ├── Settings.jsx        # Email & notification settings
│   │   │   └── ...
│   │   ├── contexts/          # Auth context
│   │   └── hooks/             # WebSocket hooks
│   └── package.json
├── requirements.txt
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Overall risk statistics |
| GET | `/api/risk-scores` | All stock risk scores |
| GET | `/api/alerts` | Recent alerts |
| GET | `/api/market-features/<symbol>` | Market features for a stock |
| GET | `/api/risk-history` | Historical risk trends |
| POST | `/api/query-rag` | AI assistant query |
| POST | `/api/backtest/run` | Run strategy backtest |
| GET | `/api/backtest/historical-analysis/<symbol>` | Historical analysis |
| POST | `/api/refresh-data` | Trigger data refresh |
| POST | `/api/auth/login` | User login (JWT) |
| POST | `/api/auth/signup` | User registration |
| GET | `/api/portfolio/holdings` | Portfolio holdings |
| GET | `/api/watchlist` | User watchlist |

## Configuration

Edit `backend/configs/config.yaml` to customize:

- **Stock universe** — 50 US tech stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, META, etc.)
- **Risk weights** — Volatility (40%), Drawdown (30%), Sentiment (20%), Liquidity (10%)
- **Agent parameters** — Feature windows, thresholds, LLM model
- **Backtesting** — Strategy parameters (MA windows, Z-score thresholds, etc.)

## License

MIT License

## Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) for market data
- [FinBERT](https://huggingface.co/ProsusAI/finbert) for financial sentiment analysis
- [Ollama](https://ollama.ai) for local LLM inference
- [LangChain](https://langchain.com) + [FAISS](https://github.com/facebookresearch/faiss) for RAG pipeline
- [Recharts](https://recharts.org) for data visualization

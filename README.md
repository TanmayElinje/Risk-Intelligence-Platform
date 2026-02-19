# Financial Risk Intelligence Platform

AI-powered stock risk monitoring platform with ML-based risk classification (XGBoost, AUC 0.79), SHAP explainability, GARCH/LSTM volatility forecasting, FinBERT sentiment analysis, and a RAG-powered AI assistant — built with React, Flask, and PostgreSQL.

## Key Results

| Component | Model/Method | Metric | Result |
|-----------|-------------|--------|--------|
| Risk Classifier | XGBoost (34 features) | AUC-ROC | **0.79** |
| Risk Classifier | 5-Fold Time-Series CV | CV AUC | **0.82 ± 0.05** |
| Explainability | SHAP TreeExplainer | Stocks Explained | **48/48** |
| Vol Forecast | GARCH(1,1) | Directional Accuracy | **79%** |
| Vol Forecast | LSTM (64→32→16) | MAE | **0.128** |
| Sentiment | FinBERT | Articles Analyzed | **400+** |
| AI Assistant | Groq llama-3.3-70B | Streaming + RAG | ✓ |

## Architecture

```
                    ┌──────────────────────────────────────┐
                    │          DATA SOURCES                 │
                    │  Yahoo Finance API · News Scraping    │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │        DATA PIPELINE                  │
                    │  yf.download() · BeautifulSoup        │
                    │  48 stocks · 5yr OHLCV · 400+ articles│
                    └──────────────┬───────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
    ┌─────────▼──────┐  ┌─────────▼──────┐  ┌──────────▼─────┐
    │ Feature Engine  │  │ FinBERT NLP    │  │ FAISS Vector   │
    │ 34 features     │  │ Sentiment      │  │ Store (RAG)    │
    │ Technical +     │  │ Headline +     │  │ 400+ articles  │
    │ Cross-sectional │  │ Content        │  │ + embeddings   │
    └─────────┬──────┘  └─────────┬──────┘  └──────────┬─────┘
              │                    │                     │
    ┌─────────▼──────────────────────────────────────────▼─────┐
    │                    ML MODELS                              │
    │  XGBoost Risk Classifier (AUC 0.79)                      │
    │  SHAP Explainability (per-stock feature contributions)   │
    │  GARCH(1,1) Volatility Forecasting (79% directional)     │
    │  LSTM Volatility Forecasting (MAE 0.128)                 │
    └─────────┬────────────────────────────────────────────────┘
              │
    ┌─────────▼──────────────────────────────────────────┐
    │              BACKEND (Flask + PostgreSQL)            │
    │  REST API · WebSocket · Groq LLM · RAG Agent        │
    └─────────┬──────────────────────────────────────────┘
              │
    ┌─────────▼──────────────────────────────────────────┐
    │              FRONTEND (React + Recharts)             │
    │  Dashboard · SHAP Explanations · AI Chat · Alerts   │
    └────────────────────────────────────────────────────┘
```

## Features

### ML & Data Science
- **XGBoost Risk Classifier** — Predicts high-volatility regimes using 34 engineered features. Trained on 5 years of data across 48 stocks with time-series aware train/test split. AUC-ROC 0.79, CV AUC 0.82.
- **SHAP Explainability** — Per-stock waterfall explanations showing exactly which features drive each risk score (e.g., "ATR pushed risk up +2.44, vol_change pushed risk down -0.20"). Critical for regulatory compliance (SR 11-7, Basel III).
- **GARCH Volatility Forecasting** — Per-stock GARCH(1,1) models with rolling backtest. 79% directional accuracy predicting whether volatility will increase or decrease.
- **LSTM Volatility Forecasting** — Deep learning model on 60-day sliding windows of 4 features. Cross-sectional training across all stocks. MAE 0.128.
- **FinBERT Sentiment Analysis** — Headline (40%) + full article content (60%) weighted sentiment scoring on 400+ scraped news articles.
- **Automated Retraining** — Single-command retrain script that runs the full ML pipeline (data → features → XGBoost → SHAP → GARCH) to keep scores calibrated.

### Platform
- **Multi-Agent Architecture** — 5 specialized agents (Market Data, Sentiment, RAG, Risk Scoring, Alert)
- **AI Financial Assistant** — Groq llama-3.3-70B with streaming responses, conversation memory, multi-stock comparison, sentiment-aware answers, and follow-up suggestions
- **RAG Knowledge Base** — FAISS vector store + real news articles for grounded explanations
- **Interactive Dashboard** — Risk overview, portfolio management, watchlist, stock comparison, historical charts
- **Advanced Analytics** — Correlation matrix, Monte Carlo simulation, Value at Risk, Markowitz optimization
- **Backtesting Engine** — 4 strategies (Buy & Hold, MA Crossover, Risk-Based, Mean Reversion) with equity curves and performance metrics
- **"Why This Risk Score?" Button** — Click on any stock to see SHAP-based feature contributions + volatility forecast
- **Email Alerts** — Configurable risk alert digests

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| ML/DS | XGBoost, scikit-learn, SHAP, arch (GARCH), TensorFlow/Keras (LSTM) |
| NLP | FinBERT (transformers + PyTorch), LangChain, FAISS |
| LLM | Groq API (llama-3.3-70B), Ollama (fallback) |
| Backend | Python 3.11+, Flask, SQLAlchemy, PostgreSQL |
| Frontend | React 18, Vite, TailwindCSS, Recharts |
| Data | yfinance, BeautifulSoup, Pandas, NumPy |

## Project Structure

```
risk-intelligence-platform/
├── backend/
│   ├── agents/                    # Multi-agent system
│   │   ├── market_agent.py        # Market feature computation
│   │   ├── sentiment_agent.py     # FinBERT sentiment analysis
│   │   ├── rag_agent.py           # RAG explanations (FAISS + LLM)
│   │   ├── risk_agent.py          # ML risk scoring (XGBoost + fallback)
│   │   └── alert_agent.py         # Alert detection + notifications
│   ├── api/
│   │   ├── app.py                 # Flask application
│   │   ├── routes.py              # API endpoints + SHAP explain
│   │   ├── backtest_routes.py     # Backtesting engine
│   │   └── portfolio_routes.py    # Portfolio & watchlist
│   ├── models/                    # Trained ML artifacts
│   │   ├── risk_classifier.joblib # XGBoost model
│   │   ├── feature_list.joblib    # 34 feature names
│   │   ├── shap_explanations.json # Per-stock SHAP explanations
│   │   ├── vol_forecasts.json     # GARCH volatility forecasts
│   │   └── model_metadata.json    # Training metrics & config
│   ├── services/
│   │   ├── ml_risk_scorer.py      # ML model inference + SHAP scoring
│   │   └── groq_client.py         # Groq LLM client
│   ├── scrapers/
│   │   ├── yfinance_collector.py  # Stock data (yf.download)
│   │   └── news_fetcher.py        # News scraping + FinBERT
│   ├── database/
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── db_service.py          # Database service layer
│   └── scripts/
│       ├── refresh_real_data.py   # Daily data refresh pipeline
│       ├── retrain_ml_model.py    # ML retrain (weekly/monthly)
│       └── rebuild_rag.py         # Rebuild FAISS vector store
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx      # Main dashboard
│       │   ├── StockDetails.jsx   # Stock detail + SHAP explain button
│       │   ├── RAGChat.jsx        # AI assistant (streaming)
│       │   ├── Backtesting.jsx    # Strategy backtesting
│       │   └── ...
│       └── services/
│           └── api.js             # API client
├── notebooks/
│   ├── 01_risk_classification_model.ipynb  # Phase 1: XGBoost (AUC 0.79)
│   ├── 02_shap_explainability.ipynb        # Phase 2: SHAP analysis
│   ├── 03_volatility_forecasting.ipynb     # Phase 3: GARCH vs LSTM
│   └── 04_eda_documentation.ipynb          # Phase 4: Complete EDA
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### 1. Clone & Setup Backend

```bash
git clone https://github.com/yourusername/risk-intelligence-platform.git
cd risk-intelligence-platform

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/risk_intelligence
GROQ_API_KEY=gsk_...    # Get from https://console.groq.com/keys
SECRET_KEY=your-secret-key
```

### 3. Setup Database

```bash
python -m backend.database.init_db
```

### 4. Train ML Models

```bash
# Automated retrain (recommended) — runs full pipeline in ~20 seconds
python -m backend.scripts.retrain_ml_model

# Or run notebooks manually for detailed analysis
jupyter notebook notebooks/01_risk_classification_model.ipynb
```

### 5. Populate Data & Run Pipeline

```bash
# Fetch real stock data + news + sentiment
python -m backend.scripts.refresh_real_data

# Build RAG knowledge base
python -m backend.scripts.rebuild_rag

# Run full pipeline (features, ML risk scores, alerts)
python -m backend.main
```

### 6. Setup Frontend

```bash
cd frontend
npm install
```

## Usage

```bash
# Terminal 1: Start Flask API
python -m backend.api.app

# Terminal 2: Start React frontend
cd frontend
npm run dev
```

Access at: `http://localhost:5173`

### Daily Operations

```bash
# Daily: fetch new data + recompute scores
python -m backend.scripts.refresh_real_data
python -m backend.main

# Weekly/Monthly: retrain ML model with latest data
python -m backend.scripts.retrain_ml_model
python -m backend.main
```

## Notebooks

| Notebook | Description | Key Result |
|----------|-------------|------------|
| `01_risk_classification_model.ipynb` | XGBoost risk classifier with 34 features. Model iteration from drawdown target (AUC 0.56) to volatility target (AUC 0.79). Includes EDA, feature engineering, 3-model comparison, time-series CV. | AUC 0.79, CV 0.82 |
| `02_shap_explainability.ipynb` | SHAP analysis: global importance, per-stock waterfalls, dependence plots, feature heatmap, force plots. Exports explanations for app integration. | 48 stocks explained |
| `03_volatility_forecasting.ipynb` | GARCH(1,1) vs LSTM comparison with rolling backtest. Per-stock forecasts and current portfolio volatility outlook. | GARCH 79% dir. acc. |
| `04_eda_documentation.ipynb` | Complete EDA: returns, fat tails, volatility clustering, correlations, drawdowns, risk-return tradeoff, sector analysis, model summary. | Full documentation |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Overall risk statistics |
| GET | `/api/risk-scores` | All stock risk scores (ML-powered) |
| GET | `/api/stock/<symbol>` | Stock detail with risk data |
| GET | `/api/stock/<symbol>/explain` | **SHAP explanation + vol forecast** |
| POST | `/api/query-rag` | AI assistant query |
| POST | `/api/query-rag-stream` | Streaming AI assistant |
| GET | `/api/alerts` | Recent alerts |
| POST | `/api/backtest/run` | Run strategy backtest |
| GET | `/api/portfolio/holdings` | Portfolio holdings |
| GET | `/api/watchlist` | User watchlist |

## Model Details

### Risk Classifier
- **Algorithm:** XGBoost with `scale_pos_weight` for class imbalance
- **Target:** High-volatility regime (top 30% of forward 21-day realized vol)
- **Features:** 34 — volatility (6), momentum (7), technical (7), volume (2), risk (5), cross-sectional (4), market regime (3)
- **Hyperparameters:** 500 trees, max_depth=5, lr=0.03, subsample=0.7, colsample=0.6

### Model Iteration
| Version | Target | AUC | Insight |
|---------|--------|-----|---------|
| v1 | Drawdown >10% in 30d | 0.56 | Too noisy — crashes are event-driven |
| v3 | High volatility (top 30%) | **0.79** | Volatility clusters — learnable signal |

### Feature Engineering (34 features)
| Category | Count | Examples |
|----------|-------|----------|
| Volatility | 6 | 21d/63d rolling vol, ATR, BB width |
| Momentum | 7 | 5/10/21/63d returns, SMA crossover |
| Technical | 7 | RSI, MACD (line/signal/histogram), Bollinger %B |
| Volume | 2 | Volume ratio, down-volume ratio |
| Risk | 5 | Max drawdown, beta, 52-week distance |
| Cross-Sectional | 4 | Volatility rank, return rank vs peers |
| Market Regime | 3 | SPY volatility, SPY return, high-vol flag |

## License

MIT License
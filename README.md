# 🧠 Financial Risk Intelligence Platform

AI-powered multi-agent system for real-time financial risk monitoring using market data, news sentiment, and explainable analytics.

## 🎯 Features

- **Multi-Agent Architecture**: Market Data, Sentiment, RAG, Risk Scoring, Alert agents
- **Real-time Risk Monitoring**: Track Nifty 50 stocks continuously
- **News Sentiment Analysis**: FinBERT-powered sentiment from MoneyControl, Economic Times
- **Explainable AI**: RAG-based explanations for risk increases
- **Interactive Dashboard**: React frontend with real-time updates
- **Production-Ready**: Logging, configuration management, modular code

## 🏗️ Architecture
```
Data Sources → Feature Engineering → Agents → Risk Score → Alerts → Dashboard
```

### Agents:
1. **MarketDataAgent**: Computes volatility, drawdown, beta, Sharpe ratio
2. **SentimentAgent**: FinBERT sentiment analysis on news
3. **NewsRAGAgent**: Vector DB + LLM for explainable insights
4. **RiskScoringAgent**: Combines signals into composite risk score
5. **AlertAgent**: Generates alerts for high-risk stocks

## 📦 Tech Stack

**Backend:**
- Python 3.11
- Flask (REST API)
- Pandas, NumPy, PySpark
- YFinance (market data)
- BeautifulSoup, Selenium (scraping)
- FinBERT (sentiment)
- LangChain, FAISS (RAG)
- Ollama/HuggingFace (LLM)

**Frontend:**
- React
- Axios
- Chart.js / Recharts
- TailwindCSS

## 🚀 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Ollama (for local LLM) - [Install here](https://ollama.ai)

### Backend Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd risk-intelligence-platform

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r backend/requirements.txt

# 5. Setup environment variables
cp backend/.env.example backend/.env

# 6. Create necessary directories
mkdir -p backend/data/{raw,processed,features,vector_db}
mkdir -p logs

# 7. Install Ollama and pull model (if using Ollama)
ollama pull llama3
```

### Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
```

## 🎯 Usage

### Run Backend
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run main pipeline
python -m backend.main

# Run Flask API (in separate terminal)
python -m backend.api.app
```

### Run Frontend
```bash
cd frontend
npm start
```

Access dashboard at: `http://localhost:3000`

## 📊 Project Structure
```
risk-intelligence-platform/
├── backend/
│   ├── agents/          # Multi-agent system
│   ├── api/             # Flask REST API
│   ├── configs/         # Configuration files
│   ├── data/            # Data storage
│   ├── scrapers/        # Web scrapers
│   ├── utils/           # Utilities
│   └── main.py          # Pipeline orchestrator
├── frontend/            # React dashboard
└── README.md
```

## 🧪 Testing
```bash
# Run tests
pytest backend/tests/

# Run with coverage
pytest --cov=backend backend/tests/
```

## 📝 Configuration

Edit `backend/configs/config.yaml` to customize:
- Stock symbols
- Agent parameters
- Risk scoring weights
- Data sources
- API settings

## 🔧 Development

Current development follows a step-by-step approach:
- ✅ Step 1: Project structure & setup
- ⏳ Step 2: Data scrapers
- ⏳ Step 3-7: Agent development
- ⏳ Step 8: Flask backend
- ⏳ Step 9: React dashboard
- ⏳ Step 10: Integration & deployment

## 📄 License

MIT License

## 👥 Contributors

[Your team]

## 🙏 Acknowledgments

- FinBERT for sentiment analysis
- Ollama for local LLM
- Nifty 50 for stock universe
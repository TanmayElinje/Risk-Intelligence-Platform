-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE
);

-- User preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(50) DEFAULT 'light',
    email_alerts BOOLEAN DEFAULT TRUE,
    email_frequency VARCHAR(50) DEFAULT 'daily',
    dashboard_layout JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stocks
CREATE TABLE stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market data (OHLCV)
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    open DECIMAL(20, 4),
    high DECIMAL(20, 4),
    low DECIMAL(20, 4),
    close DECIMAL(20, 4),
    volume BIGINT,
    adjusted_close DECIMAL(20, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- Risk scores
CREATE TABLE risk_scores (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    risk_score DECIMAL(10, 6),
    risk_level VARCHAR(20),
    risk_rank INTEGER,
    volatility_21d DECIMAL(10, 6),
    volatility_60d DECIMAL(10, 6),
    max_drawdown DECIMAL(10, 4),
    beta DECIMAL(10, 6),
    sharpe_ratio DECIMAL(10, 6),
    atr_pct DECIMAL(10, 6),
    liquidity_risk DECIMAL(10, 6),
    norm_volatility DECIMAL(10, 6),
    norm_drawdown DECIMAL(10, 6),
    norm_sentiment DECIMAL(10, 6),
    norm_liquidity DECIMAL(10, 6),
    risk_drivers TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- News articles
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    source VARCHAR(255),
    headline TEXT NOT NULL,
    description TEXT,
    url TEXT,
    published_date TIMESTAMP,
    sentiment_label VARCHAR(20),
    sentiment_score DECIMAL(10, 6),
    sentiment_confidence DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sentiment scores (aggregated)
CREATE TABLE sentiment_scores (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    avg_sentiment DECIMAL(10, 6),
    sentiment_std DECIMAL(10, 6),
    article_count INTEGER,
    positive_count INTEGER,
    negative_count INTEGER,
    neutral_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- Alerts
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    risk_score DECIMAL(10, 6),
    prev_risk_score DECIMAL(10, 6),
    risk_change DECIMAL(10, 6),
    risk_change_pct DECIMAL(10, 4),
    risk_level VARCHAR(20),
    risk_drivers TEXT,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User watchlists
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watchlist stocks (many-to-many)
CREATE TABLE watchlist_stocks (
    id SERIAL PRIMARY KEY,
    watchlist_id INTEGER REFERENCES watchlists(id) ON DELETE CASCADE,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(watchlist_id, stock_id)
);

-- User alert rules
CREATE TABLE alert_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    condition VARCHAR(50) NOT NULL, -- 'risk_above', 'risk_below', 'sentiment_negative', etc.
    threshold DECIMAL(10, 6),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User alert notifications
CREATE TABLE user_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Risk history (for trending)
CREATE TABLE risk_history (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id) ON DELETE CASCADE,
    risk_score DECIMAL(10, 6),
    risk_level VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_market_data_stock_date ON market_data(stock_id, date DESC);
CREATE INDEX idx_risk_scores_stock_date ON risk_scores(stock_id, date DESC);
CREATE INDEX idx_news_stock_date ON news_articles(stock_id, published_date DESC);
CREATE INDEX idx_sentiment_stock_date ON sentiment_scores(stock_id, date DESC);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX idx_alerts_stock ON alerts(stock_id);
CREATE INDEX idx_risk_history_stock_time ON risk_history(stock_id, timestamp DESC);
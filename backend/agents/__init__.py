"""
Agents module - Multi-agent architecture for risk intelligence
"""
from backend.agents.market_agent import MarketDataAgent
from backend.agents.sentiment_agent import SentimentAgent
from backend.agents.rag_agent import NewsRAGAgent
from backend.agents.risk_agent import RiskScoringAgent
from backend.agents.alert_agent import AlertAgent

__all__ = [
    'MarketDataAgent',
    'SentimentAgent',
    'NewsRAGAgent',
    'RiskScoringAgent',
    'AlertAgent'
]
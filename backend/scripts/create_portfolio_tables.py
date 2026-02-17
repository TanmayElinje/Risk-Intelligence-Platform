"""
Create Portfolio Tables
Run this script once to add the portfolio_holdings and portfolio_transactions tables.

Usage (from project root):
    python -m backend.scripts.create_portfolio_tables

Or directly:
    python backend/scripts/create_portfolio_tables.py
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.database.models import Base, engine, PortfolioHolding, PortfolioTransaction, EmailAlertPreference

def create_portfolio_tables():
    """Create only the new tables (won't affect existing tables)"""
    print("Creating new tables...")
    
    # This will only create tables that don't already exist
    Base.metadata.create_all(bind=engine, tables=[
        PortfolioHolding.__table__,
        PortfolioTransaction.__table__,
        EmailAlertPreference.__table__,
    ])
    
    print("✓ portfolio_holdings table created")
    print("✓ portfolio_transactions table created")
    print("✓ email_alert_preferences table created")
    print("\nAll features are ready to use!")

if __name__ == '__main__':
    create_portfolio_tables()

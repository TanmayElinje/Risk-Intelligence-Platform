"""
Initialize database with tables and seed data
"""
from backend.database.models import init_db, SessionLocal, Stock
from backend.utils import log, load_config

def seed_stocks():
    """Seed initial stock symbols"""
    log.info("Seeding stock symbols...")
    
    # Get stocks from config
    config = load_config()
    symbols = config['stocks']['symbols']
    
    # Stock metadata (sector, industry, name)
    stock_metadata = {
        'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'industry': 'Consumer Electronics'},
        'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'industry': 'Software'},
        'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'industry': 'Internet Services'},
        'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Consumer Cyclical', 'industry': 'Internet Retail'},
        'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'META': {'name': 'Meta Platforms Inc.', 'sector': 'Technology', 'industry': 'Internet Services'},
        'TSLA': {'name': 'Tesla Inc.', 'sector': 'Consumer Cyclical', 'industry': 'Auto Manufacturers'},
        'NFLX': {'name': 'Netflix Inc.', 'sector': 'Communication Services', 'industry': 'Entertainment'},
        'ADBE': {'name': 'Adobe Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'CRM': {'name': 'Salesforce Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'ORCL': {'name': 'Oracle Corporation', 'sector': 'Technology', 'industry': 'Software'},
        'CSCO': {'name': 'Cisco Systems Inc.', 'sector': 'Technology', 'industry': 'Communication Equipment'},
        'INTC': {'name': 'Intel Corporation', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'AMD': {'name': 'Advanced Micro Devices', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'QCOM': {'name': 'Qualcomm Inc.', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'TXN': {'name': 'Texas Instruments', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'AVGO': {'name': 'Broadcom Inc.', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'INTU': {'name': 'Intuit Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'AMAT': {'name': 'Applied Materials', 'sector': 'Technology', 'industry': 'Semiconductor Equipment'},
        'LRCX': {'name': 'Lam Research', 'sector': 'Technology', 'industry': 'Semiconductor Equipment'},
        'MU': {'name': 'Micron Technology', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'KLAC': {'name': 'KLA Corporation', 'sector': 'Technology', 'industry': 'Semiconductor Equipment'},
        'SNPS': {'name': 'Synopsys Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'CDNS': {'name': 'Cadence Design Systems', 'sector': 'Technology', 'industry': 'Software'},
        'MCHP': {'name': 'Microchip Technology', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'MRVL': {'name': 'Marvell Technology', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'NXPI': {'name': 'NXP Semiconductors', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'ADI': {'name': 'Analog Devices', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'SWKS': {'name': 'Skyworks Solutions', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'QRVO': {'name': 'Qorvo Inc.', 'sector': 'Technology', 'industry': 'Semiconductors'},
        'UBER': {'name': 'Uber Technologies', 'sector': 'Technology', 'industry': 'Internet Services'},
        'ABNB': {'name': 'Airbnb Inc.', 'sector': 'Consumer Cyclical', 'industry': 'Travel Services'},
        'SNOW': {'name': 'Snowflake Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'ZM': {'name': 'Zoom Video Communications', 'sector': 'Technology', 'industry': 'Software'},
        'DOCU': {'name': 'DocuSign Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'SHOP': {'name': 'Shopify Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'SQ': {'name': 'Block Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'COIN': {'name': 'Coinbase Global', 'sector': 'Financial Services', 'industry': 'Financial Data & Stock Exchanges'},
        'RBLX': {'name': 'Roblox Corporation', 'sector': 'Communication Services', 'industry': 'Electronic Gaming'},
        'DDOG': {'name': 'Datadog Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'NET': {'name': 'Cloudflare Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'CRWD': {'name': 'CrowdStrike Holdings', 'sector': 'Technology', 'industry': 'Software'},
        'ZS': {'name': 'Zscaler Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'PANW': {'name': 'Palo Alto Networks', 'sector': 'Technology', 'industry': 'Software'},
        'FTNT': {'name': 'Fortinet Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'OKTA': {'name': 'Okta Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'SPLK': {'name': 'Splunk Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'NOW': {'name': 'ServiceNow Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'WDAY': {'name': 'Workday Inc.', 'sector': 'Technology', 'industry': 'Software'},
        'TEAM': {'name': 'Atlassian Corporation', 'sector': 'Technology', 'industry': 'Software'},
    }
    
    db = SessionLocal()
    try:
        for symbol in symbols:
            existing = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not existing:
                metadata = stock_metadata.get(symbol, {
                    'name': symbol,
                    'sector': 'Technology',
                    'industry': 'Technology'
                })
                stock = Stock(symbol=symbol, **metadata)
                db.add(stock)
        
        db.commit()
        log.info(f"✓ Seeded {len(symbols)} stocks")
    except Exception as e:
        db.rollback()
        log.error(f"Error seeding stocks: {str(e)}")
    finally:
        db.close()

def main():
    """Main initialization"""
    log.info("=" * 60)
    log.info("INITIALIZING DATABASE")
    log.info("=" * 60)
    
    # Create tables
    init_db()
    
    # Seed data
    seed_stocks()
    
    log.info("=" * 60)
    log.info("✓ DATABASE INITIALIZED SUCCESSFULLY")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
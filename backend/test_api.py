"""
Test API endpoints
"""
import requests
import json
from backend.utils import log

BASE_URL = "http://localhost:5000/api"

def test_endpoint(method, endpoint, data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        log.info(f"\n{'='*60}")
        log.info(f"{method} {endpoint}")
        log.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            log.info(f"Response: {json.dumps(result, indent=2)[:500]}...")
        else:
            log.error(f"Error: {response.text}")
        
        return response
        
    except Exception as e:
        log.error(f"Failed to test {endpoint}: {str(e)}")
        return None

def main():
    """Test all API endpoints"""
    log.info("=" * 60)
    log.info("TESTING API ENDPOINTS")
    log.info("=" * 60)
    
    # Test health check
    test_endpoint('GET', '/health')
    
    # Test stats
    test_endpoint('GET', '/stats')
    
    # Test risk scores
    test_endpoint('GET', '/risk-scores?limit=5')
    
    # Test top risks
    test_endpoint('GET', '/top-risks?limit=5')
    
    # Test stock details (use first stock)
    test_endpoint('GET', '/stock/AAPL')
    
    # Test alerts
    test_endpoint('GET', '/alerts?limit=5')
    
    # Test sentiment trends
    test_endpoint('GET', '/sentiment-trends?days=7')
    
    # Test market features
    test_endpoint('GET', '/market-features/AAPL?days=30')
    
    # Test RAG query
    test_endpoint('POST', '/query-rag', {
        'query': 'Why is AAPL risk high?',
        'stock_symbol': 'AAPL'
    })
    
    log.info("\n" + "=" * 60)
    log.info("✓ API TESTING COMPLETE")
    log.info("=" * 60)

if __name__ == "__main__":
    main()
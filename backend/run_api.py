"""
Run the Flask API server with WebSocket support
"""
from backend.utils import log

if __name__ == '__main__':
    # Import here to avoid circular imports
    from backend.api.app import run_server
    
    try:
        run_server(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    except KeyboardInterrupt:
        log.info("\n✓ Server stopped by user")
    except Exception as e:
        log.error(f"Server error: {str(e)}")
        import traceback
        traceback.print_exc()
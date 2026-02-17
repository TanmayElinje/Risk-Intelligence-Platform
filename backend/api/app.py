"""
Flask API Application with WebSocket support
"""
from flask import Flask, request, jsonify
from backend.utils import log, load_config
from backend.websocket.socket_manager import socket_manager
from dotenv import load_dotenv
import os

# Load .env file early
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = load_config()
    
    # Manual CORS handler for OPTIONS requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
            return response, 200
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response
    
    # Initialize WebSocket
    socket_manager.init_app(app)
    
    # Register Blueprint routes
    from backend.api.routes import api_bp
    from backend.api.auth_routes import auth_bp
    from backend.api.watchlist_routes import watchlist_bp
    from backend.api.portfolio_routes import portfolio_bp
    from backend.api.email_routes import email_bp
    from backend.api.advanced_analytics_routes import advanced_bp
    from backend.api.backtest_routes import backtest_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(advanced_bp)
    app.register_blueprint(backtest_bp)
    
    log.info("Flask app created successfully")
    log.info("CORS enabled (manual handlers)")
    log.info("WebSocket enabled")
    log.info("API routes registered")
    
    return app

def run_server(host='0.0.0.0', port=5000, debug=True):
    """Run the Flask server with WebSocket support"""
    app = create_app()
    
    log.info("=" * 60)
    log.info("STARTING FLASK API SERVER WITH WEBSOCKET")
    log.info("=" * 60)
    log.info(f"Host: {host}")
    log.info(f"Port: {port}")
    log.info(f"Debug: {debug}")
    log.info("=" * 60)
    
    # Use SocketIO run instead of app.run
    socket_manager.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_server()
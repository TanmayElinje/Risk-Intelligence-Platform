"""
Flask API Application with WebSocket support
"""
from flask import Flask
from flask_cors import CORS
from backend.utils import log, load_config
from backend.websocket.socket_manager import socket_manager

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = load_config()
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/socket.io/*": {"origins": "*"}
    })
    
    # Initialize WebSocket
    socket_manager.init_app(app)
    
    # Register Blueprint routes
    from backend.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    log.info("Flask app created successfully")
    log.info("CORS enabled for all origins")
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
"""
Flask API Application
"""
from flask import Flask
from flask_cors import CORS
from backend.utils import log, load_config

def create_app():
    """
    Create and configure Flask application
    
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = load_config()
    api_config = config['api']
    
    # Configure CORS
    CORS(app, origins=api_config['cors_origins'])
    
    # Register blueprints
    from backend.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    log.info("Flask app created successfully")
    log.info(f"CORS enabled for: {api_config['cors_origins']}")
    
    return app

def run_server():
    """Run Flask development server"""
    config = load_config()
    api_config = config['api']
    
    app = create_app()
    
    log.info("=" * 60)
    log.info("STARTING FLASK API SERVER")
    log.info("=" * 60)
    log.info(f"Host: {api_config['host']}")
    log.info(f"Port: {api_config['port']}")
    log.info(f"Debug: {api_config['debug']}")
    log.info("=" * 60)
    
    app.run(
        host=api_config['host'],
        port=api_config['port'],
        debug=api_config['debug']
    )

if __name__ == '__main__':
    run_server()
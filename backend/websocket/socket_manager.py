"""
WebSocket Manager - Real-time updates using Flask-SocketIO
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from backend.utils import log
import threading
import time
from datetime import datetime

class SocketManager:
    """
    Manages WebSocket connections and real-time broadcasts
    """
    
    def __init__(self, app=None):
        self.socketio = None
        self.app = app
        self.connected_clients = set()
        self.update_thread = None
        self.running = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize SocketIO with Flask app"""
        self.app = app
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='eventlet',
            logger=True,
            engineio_logger=False
        )
        
        # Register event handlers
        self.register_handlers()
        
        log.info("✓ SocketIO initialized")
    
    def register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            log.info(f"Client connected: {threading.current_thread().name}")
            self.connected_clients.add(threading.current_thread().name)
            
            # Send welcome message
            emit('connection_status', {
                'status': 'connected',
                'message': 'Connected to Risk Intelligence Platform',
                'timestamp': datetime.now().isoformat()
            })
            
            # Send current stats immediately
            self.broadcast_stats()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            log.info(f"Client disconnected: {threading.current_thread().name}")
            self.connected_clients.discard(threading.current_thread().name)
        
        @self.socketio.on('subscribe_stock')
        def handle_subscribe(data):
            """Subscribe to specific stock updates"""
            symbol = data.get('symbol')
            if symbol:
                join_room(f'stock_{symbol}')
                log.info(f"Client subscribed to {symbol}")
                emit('subscribed', {'symbol': symbol})
        
        @self.socketio.on('unsubscribe_stock')
        def handle_unsubscribe(data):
            """Unsubscribe from stock updates"""
            symbol = data.get('symbol')
            if symbol:
                leave_room(f'stock_{symbol}')
                log.info(f"Client unsubscribed from {symbol}")
                emit('unsubscribed', {'symbol': symbol})
        
        @self.socketio.on('request_stats')
        def handle_stats_request():
            """Client requests current stats"""
            self.broadcast_stats()
    
    def broadcast_stats(self):
        """Broadcast current platform stats"""
        try:
            from backend.database import DatabaseService
            from backend.database.models import Stock, Alert
            
            with DatabaseService() as db:
                # Get latest stats
                stocks = db.db.query(Stock).all()
                
                # High risk count
                high_risk_count = sum(1 for s in stocks if s.risk_score and s.risk_score > 0.6)
                
                # Recent alerts
                recent_alerts = db.db.query(Alert).order_by(
                    Alert.created_at.desc()
                ).limit(5).all()
                
                stats = {
                    'total_stocks': len(stocks),
                    'high_risk_stocks': high_risk_count,
                    'recent_alerts_count': len(recent_alerts),
                    'timestamp': datetime.now().isoformat()
                }
                
                self.socketio.emit('stats_update', stats)
                
        except Exception as e:
            log.error(f"Error broadcasting stats: {str(e)}")
    
    def broadcast_risk_update(self, symbol: str, risk_score: float, risk_level: str):
        """Broadcast risk score update for specific stock"""
        try:
            data = {
                'symbol': symbol,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'timestamp': datetime.now().isoformat()
            }
            
            # Broadcast to all clients
            self.socketio.emit('risk_update', data)
            
            # Broadcast to stock-specific room
            self.socketio.emit('risk_update', data, room=f'stock_{symbol}')
            
            log.info(f"Broadcasted risk update: {symbol} = {risk_score:.3f}")
            
        except Exception as e:
            log.error(f"Error broadcasting risk update: {str(e)}")
    
    def broadcast_alert(self, alert_data: dict):
        """Broadcast new alert to all clients"""
        try:
            self.socketio.emit('new_alert', {
                'id': alert_data.get('id'),
                'symbol': alert_data.get('symbol'),
                'type': alert_data.get('alert_type'),
                'severity': alert_data.get('severity'),
                'message': alert_data.get('message'),
                'risk_score': alert_data.get('risk_score'),
                'timestamp': alert_data.get('timestamp', datetime.now().isoformat())
            })
            
            log.info(f"Broadcasted alert: {alert_data.get('symbol')} - {alert_data.get('alert_type')}")
            
        except Exception as e:
            log.error(f"Error broadcasting alert: {str(e)}")
    
    def start_background_updates(self, interval: int = 30):
        """Start background thread for periodic updates"""
        if self.running:
            log.warning("Background updates already running")
            return
        
        self.running = True
        
        def update_loop():
            log.info(f"Starting background updates (interval: {interval}s)")
            
            while self.running:
                try:
                    if len(self.connected_clients) > 0:
                        # Broadcast stats every interval
                        self.broadcast_stats()
                        
                        # Could add more periodic updates here
                        # e.g., check for new alerts, risk changes, etc.
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    log.error(f"Error in update loop: {str(e)}")
                    time.sleep(interval)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        
        log.info("✓ Background update thread started")
    
    def stop_background_updates(self):
        """Stop background updates"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        log.info("✓ Background updates stopped")
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Run the SocketIO server"""
        log.info("=" * 60)
        log.info("STARTING WEBSOCKET SERVER")
        log.info("=" * 60)
        log.info(f"Host: {host}")
        log.info(f"Port: {port}")
        log.info("=" * 60)
        
        # Start background updates
        self.start_background_updates(interval=30)
        
        # Run server
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False  # Important: disable reloader with eventlet
        )

# Global instance
socket_manager = SocketManager()
import multiprocessing

# Bind to PORT env var (Render sets this)
bind = "0.0.0.0:10000"
workers = 1  # Single worker for WebSocket + ML model memory
worker_class = "eventlet"
timeout = 120  # ML scoring can take time
keepalive = 5
errorlog = "-"
accesslog = "-"
loglevel = "info"

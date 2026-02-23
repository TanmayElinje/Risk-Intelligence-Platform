#!/bin/bash
# ============================================================
# Oracle Cloud VM Deployment Script
# Risk Intelligence Platform
#
# Run as: bash deploy.sh
# On: Ubuntu 22.04 ARM (Oracle Cloud Free Tier)
# ============================================================

set -e  # Exit on error

echo "============================================================"
echo "  RISK INTELLIGENCE PLATFORM — DEPLOYMENT"
echo "  $(date)"
echo "============================================================"

# ============================================================
# STEP 1: System packages
# ============================================================
echo ""
echo "[1/9] Installing system packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3.11 python3.11-venv python3.11-dev \
    python3-pip \
    nodejs npm \
    postgresql postgresql-contrib \
    nginx certbot python3-certbot-nginx \
    git curl wget build-essential \
    libpq-dev libffi-dev

# Use python3.11 as default if available
if command -v python3.11 &> /dev/null; then
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
fi

# Update npm
sudo npm install -g n
sudo n lts
echo "✓ System packages installed"

# ============================================================
# STEP 2: PostgreSQL setup
# ============================================================
echo ""
echo "[2/9] Setting up PostgreSQL..."

# Generate a random password
DB_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)

sudo -u postgres psql -c "CREATE USER riskapp WITH PASSWORD '${DB_PASSWORD}';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE risk_intelligence OWNER riskapp;" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE risk_intelligence TO riskapp;"

echo "✓ PostgreSQL configured"
echo "  Database: risk_intelligence"
echo "  User: riskapp"
echo "  Password: ${DB_PASSWORD}"

# ============================================================
# STEP 3: Clone repository
# ============================================================
echo ""
echo "[3/9] Setting up application..."

APP_DIR="/home/ubuntu/risk-intelligence-platform"

if [ -d "$APP_DIR" ]; then
    echo "  Updating existing repo..."
    cd $APP_DIR
    git pull
else
    echo "  Enter your GitHub repo URL:"
    read -p "  > " REPO_URL
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# ============================================================
# STEP 4: Python environment
# ============================================================
echo ""
echo "[4/9] Setting up Python environment..."

cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Python environment ready"

# ============================================================
# STEP 5: Environment variables
# ============================================================
echo ""
echo "[5/9] Configuring environment..."

# Prompt for Groq API key
echo "  Enter your Groq API key (from https://console.groq.com/keys):"
read -p "  > " GROQ_KEY

SECRET_KEY=$(openssl rand -base64 32)

cat > backend/.env << EOF
DATABASE_URL=postgresql://riskapp:${DB_PASSWORD}@localhost:5432/risk_intelligence
GROQ_API_KEY=${GROQ_KEY}
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production
FLASK_DEBUG=False
EOF

echo "✓ Environment configured"

# ============================================================
# STEP 6: Initialize database + train ML model
# ============================================================
echo ""
echo "[6/9] Initializing database & training ML model..."

cd $APP_DIR
source venv/bin/activate

python -m backend.database.init_db
echo "✓ Database initialized"

python -m backend.scripts.retrain_ml_model
echo "✓ ML model trained"

python -m backend.scripts.refresh_real_data
echo "✓ Real data loaded"

python -m backend.scripts.rebuild_rag
echo "✓ RAG vector store built"

python -m backend.main
echo "✓ Pipeline complete"

# ============================================================
# STEP 7: Build frontend
# ============================================================
echo ""
echo "[7/9] Building frontend..."

cd $APP_DIR/frontend

# Get server's public IP
PUBLIC_IP=$(curl -s ifconfig.me)

# Create production env
cat > .env.production << EOF
VITE_API_URL=http://${PUBLIC_IP}/api
EOF

npm install
npm run build

echo "✓ Frontend built"

# ============================================================
# STEP 8: Nginx reverse proxy
# ============================================================
echo ""
echo "[8/9] Configuring Nginx..."

sudo tee /etc/nginx/sites-available/risk-intelligence << EOF
server {
    listen 80;
    server_name ${PUBLIC_IP};

    # Frontend (React static files)
    location / {
        root ${APP_DIR}/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # WebSocket proxy
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }

    # Query RAG streaming (needs longer timeout)
    location /api/query-rag-stream {
        proxy_pass http://127.0.0.1:5000/api/query-rag-stream;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host \$host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/risk-intelligence /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "✓ Nginx configured"

# ============================================================
# STEP 9: Systemd service (auto-start on reboot)
# ============================================================
echo ""
echo "[9/9] Creating systemd service..."

sudo tee /etc/systemd/system/risk-intelligence.service << EOF
[Unit]
Description=Risk Intelligence Platform API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=${APP_DIR}
Environment=PATH=${APP_DIR}/venv/bin:/usr/bin
ExecStart=${APP_DIR}/venv/bin/python -m backend.api.app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable risk-intelligence
sudo systemctl start risk-intelligence

echo "✓ Service created and started"

# ============================================================
# DONE
# ============================================================
echo ""
echo "============================================================"
echo "  ✓ DEPLOYMENT COMPLETE!"
echo "============================================================"
echo ""
echo "  Dashboard:  http://${PUBLIC_IP}"
echo "  API:        http://${PUBLIC_IP}/api/stats"
echo "  DB Pass:    ${DB_PASSWORD}"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status risk-intelligence   # Check status"
echo "    sudo systemctl restart risk-intelligence   # Restart"
echo "    sudo journalctl -u risk-intelligence -f    # View logs"
echo ""
echo "  Daily refresh runs automatically at 08:00 AM"
echo "  To retrain ML model: cd ${APP_DIR} && source venv/bin/activate && python -m backend.scripts.retrain_ml_model"
echo "============================================================"
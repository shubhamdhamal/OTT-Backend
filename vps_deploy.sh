#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  OTT Backend — MilesWeb Linux VPS Deployment Script
#  OS: Ubuntu 22.04 LTS
#  Stack: Docker + Docker Compose + Nginx (reverse proxy) + Certbot (SSL)
#
#  Usage:
#    1. SSH into your VPS as root
#    2. Upload this script:  scp vps_deploy.sh root@<VPS-IP>:~
#    3. Run:                 bash vps_deploy.sh
#    4. Follow the printed Next Steps at the end
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

APP_DIR="/opt/ott-backend"
NGINX_CONF="/etc/nginx/sites-available/ott-backend"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERR]${NC}  $1"; exit 1; }

[ "$EUID" -ne 0 ] && error "Run as root: sudo bash vps_deploy.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OTT Backend — MilesWeb VPS Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 1. System update ─────────────────────────────────────────────────────────
info "Updating system packages..."
apt-get update -q && apt-get upgrade -y -q
success "System updated"

# ── 2. Install runtime deps ──────────────────────────────────────────────────
info "Installing Nginx, Certbot, UFW, Fail2Ban..."
apt-get install -y -q \
    nginx \
    certbot python3-certbot-nginx \
    ufw \
    fail2ban \
    curl wget git htop unzip
success "System packages installed"

# ── 3. Install Docker ────────────────────────────────────────────────────────
if command -v docker &>/dev/null; then
    warn "Docker already installed ($(docker --version)). Skipping."
else
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    success "Docker installed"
fi

# Docker Compose plugin (v2)
if docker compose version &>/dev/null; then
    warn "Docker Compose already available. Skipping."
else
    info "Installing Docker Compose plugin..."
    apt-get install -y -q docker-compose-plugin
    success "Docker Compose installed"
fi

# ── 4. Create app directory ──────────────────────────────────────────────────
info "Creating app directory $APP_DIR..."
mkdir -p "$APP_DIR"
success "Directory ready"

# ── 5. Firewall ──────────────────────────────────────────────────────────────
info "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    comment 'SSH'
ufw allow 80/tcp    comment 'HTTP'
ufw allow 443/tcp   comment 'HTTPS'
ufw --force enable
success "Firewall configured (22/80/443 open)"

# ── 6. Fail2Ban ──────────────────────────────────────────────────────────────
info "Configuring Fail2Ban..."
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true
EOF
systemctl enable fail2ban
systemctl restart fail2ban
success "Fail2Ban configured"

# ── 7. Nginx — reverse proxy ─────────────────────────────────────────────────
info "Writing Nginx config..."
cat > "$NGINX_CONF" <<'NGINX'
# OTT Backend — Nginx Reverse Proxy
# Replace YOUR_DOMAIN with your actual domain before running certbot

upstream ott_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name YOUR_DOMAIN www.YOUR_DOMAIN;

    # Large video uploads — must match Django DATA_UPLOAD_MAX_MEMORY_SIZE (5GB)
    # Admin uploads can reach 2-3 GB; set to 5G to give headroom
    client_max_body_size 5G;
    client_body_timeout  3600s;

    access_log /var/log/nginx/ott-backend-access.log;
    error_log  /var/log/nginx/ott-backend-error.log warn;

    # Django static files
    location /static/ {
        alias /opt/ott-backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django media files (uploaded originals — not HLS, those are on R2)
    location /media/ {
        alias /opt/ott-backend/media/;
        expires 7d;
    }

    # API / Django
    location / {
        proxy_pass         http://ott_backend;
        proxy_http_version 1.1;
        proxy_set_header   Connection        "";
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # Long timeouts for large video uploads + Celery task polling
        proxy_read_timeout    600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout    600s;

        # Stream uploads directly to backend (no nginx buffering)
        proxy_request_buffering off;
        proxy_buffering         off;
    }
}
NGINX

ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/ott-backend
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
success "Nginx configured"

# ── 8. SSH hardening ─────────────────────────────────────────────────────────
info "Hardening SSH..."
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/'   /etc/ssh/sshd_config
sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/'      /etc/ssh/sshd_config
systemctl restart sshd
success "SSH hardened (key-only login, no root password login)"

# ── 9. Print next steps ───────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}  VPS base setup complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${CYAN}NEXT STEPS — run these after this script finishes:${NC}"
echo ""
echo "  ── Step 1: Upload your app ──"
echo "  From your local machine:"
echo "  rsync -avz --exclude venv --exclude .git --exclude __pycache__ \\"
echo "    ./OTT-Backend/ root@<VPS-IP>:$APP_DIR/"
echo ""
echo "  ── Step 2: Create .env ──"
echo "  cd $APP_DIR"
echo "  cp .env.example .env"
echo "  nano .env          # fill in all values"
echo ""
echo "  ── Step 3: Update Nginx domain ──"
echo "  nano $NGINX_CONF"
echo "  # Replace YOUR_DOMAIN with your actual domain (e.g. api.myapp.com)"
echo "  nginx -t && systemctl reload nginx"
echo ""
echo "  ── Step 4: Build & start containers ──"
echo "  cd $APP_DIR"
echo "  docker compose build --no-cache"
echo "  docker compose up -d"
echo "  docker compose logs -f            # watch startup logs"
echo ""
echo "  ── Step 5: SSL certificate ──"
echo "  certbot --nginx -d your-domain.com -d www.your-domain.com"
echo "  # Auto-renewal is set up by certbot automatically"
echo ""
echo "  ── Step 6: Verify ──"
echo "  docker compose ps                 # all services should be Up"
echo "  curl https://your-domain.com/api/v1/"
echo ""
echo -e "${CYAN}USEFUL COMMANDS:${NC}"
echo "  docker compose logs -f web        # Django logs"
echo "  docker compose logs -f celery     # Celery worker logs"
echo "  docker compose restart web        # restart Django"
echo "  docker compose exec web python manage.py createsuperuser"
echo "  docker compose exec web python manage.py shell"
echo "  docker compose down && docker compose up -d   # full restart"
echo ""
echo -e "${YELLOW}FILES:${NC}"
echo "  App dir:     $APP_DIR"
echo "  Nginx conf:  $NGINX_CONF"
echo "  Nginx logs:  /var/log/nginx/ott-backend-*.log"
echo ""

# Update system
echo "📦 Updating system..."
apt update && apt upgrade -y

# Install dependencies
echo "📥 Installing dependencies..."
apt install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    ffmpeg \
    nginx \
    curl \
    wget \
    git \
    htop \
    certbot \
    python3-certbot-nginx

# Create directories
echo "📁 Creating directories..."
mkdir -p /var/media/uploads
mkdir -p /var/log
mkdir -p /tmp/hls_videos
chmod 777 /tmp/hls_videos

# Setup PostgreSQL
echo "🗄️  Setting up PostgreSQL..."
sudo -u postgres psql << EOF
CREATE DATABASE ott_backend;
CREATE USER django WITH PASSWORD 'change_me_123!';
ALTER ROLE django SET client_encoding TO 'utf8';
ALTER ROLE django SET default_transaction_isolation TO 'read committed';
ALTER ROLE django SET default_transaction_deferrable TO off;
ALTER ROLE django SET default_transaction_read_uncommitted TO on;
ALTER ROLE django SET default_transaction_read_committed TO on;
GRANT ALL PRIVILEGES ON DATABASE ott_backend TO django;
\q
EOF

echo "✅ PostgreSQL setup complete"
echo "   Database: ott_backend"
echo "   User: django"
echo "   ⚠️  CHANGE PASSWORD in .env file!"

# Setup firewall
echo "🔒 Setting up firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "✅ Firewall configured"

# Create systemd service for Gunicorn
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/ott-backend.service << 'EOF'
[Unit]
Description=OTT Backend Django Service
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/ott-backend
Environment="PATH=/opt/ott-backend/venv/bin"
EnvironmentFile=/opt/ott-backend/.env
ExecStart=/opt/ott-backend/venv/bin/gunicorn \
    --workers 4 \
    --timeout 1800 \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/gunicorn-access.log \
    --error-logfile /var/log/gunicorn-error.log \
    ott_backend.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "✅ Systemd service created"

# Create Nginx configuration template
echo "🌐 Creating Nginx configuration..."
cat > /etc/nginx/sites-available/ott-backend << 'EOF'
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 5G;
    
    access_log /var/log/nginx/ott-backend-access.log;
    error_log /var/log/nginx/ott-backend-error.log;
    
    location /static/ {
        alias /opt/ott-backend/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /var/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Long timeout for encoding uploads
        proxy_read_timeout 1800s;
        proxy_connect_timeout 1800s;
        proxy_send_timeout 1800s;
        
        # Buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/ott-backend /etc/nginx/sites-enabled/ott-backend
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl restart nginx
echo "✅ Nginx configured"

# Create SSH hardening script
echo "🔐 Hardening SSH..."
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

systemctl restart sshd
echo "✅ SSH hardened"

# Install Fail2Ban
echo "🛡️  Installing Fail2Ban..."
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban

cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true
EOF

systemctl restart fail2ban
echo "✅ Fail2Ban configured"

# Create deployment guide
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ VPS Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next Steps:"
echo ""
echo "1. Upload your application to /opt/ott-backend"
echo "   scp -r ./OTT-Backend/* root@your-vps:/opt/ott-backend/"
echo ""
echo "2. Create .env file with R2 credentials"
echo "   nano /opt/ott-backend/.env"
echo ""
echo "   Required variables:"
echo "   - R2_ACCOUNT_ID"
echo "   - R2_ACCESS_KEY_ID"
echo "   - R2_SECRET_ACCESS_KEY"
echo "   - DB_PASSWORD (change from: change_me_123!)"
echo "   - SECRET_KEY (generate a new one)"
echo ""
echo "3. Setup application"
echo "   cd /opt/ott-backend"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r HLS_REQUIREMENTS.txt"
echo "   python manage.py migrate"
echo "   python manage.py createsuperuser"
echo "   python manage.py collectstatic --noinput"
echo ""
echo "4. Set ownership"
echo "   chown -R www-data:www-data /opt/ott-backend"
echo "   chown -R www-data:www-data /var/media"
echo ""
echo "5. Start service"
echo "   systemctl start ott-backend"
echo "   systemctl enable ott-backend"
echo ""
echo "6. Setup SSL certificate"
echo "   certbot --nginx -d your-domain.com"
echo ""
echo "7. Monitor service"
echo "   systemctl status ott-backend"
echo "   tail -f /var/log/gunicorn-error.log"
echo ""
echo "Database Info:"
echo "   Database: ott_backend"
echo "   User: django"
echo "   ⚠️  UPDATE PASSWORD IN .env FILE!"
echo ""
echo "Generated Files:"
echo "   - Systemd service: /etc/systemd/system/ott-backend.service"
echo "   - Nginx config: /etc/nginx/sites-available/ott-backend"
echo "   - SSH config: /etc/ssh/sshd_config (hardened)"
echo ""
echo "Test Commands:"
echo "   # Check FFmpeg"
echo "   ffmpeg -version"
echo "   # Check PostgreSQL"
echo "   sudo -u postgres psql -c \"SELECT version();\"" 
echo "   # Check Nginx"
echo "   curl http://localhost/"
echo ""
echo "Support:"
echo "   Documentation: /opt/ott-backend/*.md"
echo "   Logs: /var/log/hls_streaming.log"
echo ""

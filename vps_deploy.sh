#!/bin/bash
# =============================================================================
#  OTT Backend - MilesWeb Linux VPS Deployment Script
#  OS: Ubuntu 22.04 LTS
#  Stack: Docker + Docker Compose + Nginx (reverse proxy) + Certbot (SSL)
#
#  Usage:
#    1. SSH into your VPS as root
#    2. Upload this script:  scp vps_deploy.sh root@<VPS-IP>:~
#    3. Run:                 bash vps_deploy.sh
#    4. Follow the printed Next Steps at the end
# =============================================================================

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
echo "====================================================="
echo "  OTT Backend - MilesWeb VPS Setup"
echo "====================================================="
echo ""

# -- 1. System update --------------------------------------------------------
info "Updating system packages..."
apt-get update -q && apt-get upgrade -y -q
success "System updated"

# -- 2. Install runtime deps --------------------------------------------------
info "Installing Nginx, Certbot, UFW, Fail2Ban..."
apt-get install -y -q \
    nginx \
    certbot python3-certbot-nginx \
    ufw \
    fail2ban \
    curl wget git htop unzip
success "System packages installed"

# -- 3. Install Docker --------------------------------------------------------
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

# -- 4. Create app directory --------------------------------------------------
info "Creating app directory $APP_DIR..."
mkdir -p "$APP_DIR"
success "Directory ready"

# -- 5. Firewall --------------------------------------------------------------
info "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    comment 'SSH'
ufw allow 80/tcp    comment 'HTTP'
ufw allow 443/tcp   comment 'HTTPS'
ufw --force enable
success "Firewall configured (22/80/443 open)"

# -- 6. Fail2Ban --------------------------------------------------------------
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

# -- 7. Nginx reverse proxy ---------------------------------------------------
info "Writing Nginx config..."
cat > "$NGINX_CONF" <<'NGINX'
upstream ott_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name YOUR_DOMAIN www.YOUR_DOMAIN;

    # Large video uploads - must match Django DATA_UPLOAD_MAX_MEMORY_SIZE (5GB)
    # Admin uploads can reach 2-3 GB; 5G gives safe headroom
    client_max_body_size 5G;
    client_body_timeout  3600s;

    access_log /var/log/nginx/ott-backend-access.log;
    error_log  /var/log/nginx/ott-backend-error.log warn;

    location /static/ {
        alias /opt/ott-backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /opt/ott-backend/media/;
        expires 7d;
    }

    location / {
        proxy_pass         http://ott_backend;
        proxy_http_version 1.1;
        proxy_set_header   Connection        "";
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # Long timeouts for large video uploads + Celery task polling
        proxy_read_timeout    3600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout    3600s;

        # Stream uploads directly (no nginx buffering)
        proxy_request_buffering off;
        proxy_buffering         off;
    }
}
NGINX

ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/ott-backend
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
success "Nginx configured"

# -- 8. SSH hardening (optional) ---------------------------------------------
# WARNING: Enabling this without a working SSH key can lock you out.
# Enable only after you verify key-based login works.
if [ "${ENABLE_SSH_HARDENING:-false}" = "true" ]; then
    info "Hardening SSH (ENABLE_SSH_HARDENING=true)..."
    sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
    sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/'   /etc/ssh/sshd_config
    sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/'      /etc/ssh/sshd_config
    systemctl restart sshd
    success "SSH hardened (key-only login, no root password login)"
else
    warn "Skipping SSH hardening (set ENABLE_SSH_HARDENING=true to enable)."
fi

# -- 9. Print next steps ------------------------------------------------------
echo ""
echo "====================================================="
echo -e "${GREEN}  VPS base setup complete!${NC}"
echo "====================================================="
echo ""
echo -e "${CYAN}NEXT STEPS:${NC}"
echo ""
echo "  1. Clone your repo onto the VPS:"
echo "     cd $APP_DIR"
echo "     git clone https://github.com/<YOU>/<REPO>.git ."
echo "     cd OTT-Backend"
echo ""
echo "  2. Create .env:"
echo "     cp .env.example .env"
echo "     nano .env   # fill in all values"
echo ""
echo "  3. Set your domain in Nginx:"
echo "     nano $NGINX_CONF"
echo "     # Replace YOUR_DOMAIN with e.g. api.myapp.com"
echo "     nginx -t && systemctl reload nginx"
echo ""
echo "  4. Build & start containers:"
echo "     docker compose build --no-cache"
echo "     docker compose up -d"
echo "     docker compose logs -f"
echo ""
echo "  5. Migrations + superuser:"
echo "     docker compose exec web python manage.py migrate"
echo "     docker compose exec web python manage.py createsuperuser"
echo ""
echo "  6. SSL:"
echo "     certbot --nginx -d your-domain.com"
echo ""
echo "  7. Verify:"
echo "     docker compose ps"
echo "     curl https://your-domain.com/api/v1/"
echo ""
echo -e "${CYAN}USEFUL COMMANDS:${NC}"
echo "  docker compose logs -f web"
echo "  docker compose logs -f celery"
echo "  docker compose restart web"
echo "  docker compose exec web python manage.py createsuperuser"
echo "  docker compose down && docker compose up -d"
echo ""
echo -e "${YELLOW}FILES:${NC}"
echo "  App dir:    $APP_DIR"
echo "  Nginx conf: $NGINX_CONF"
echo "  Nginx logs: /var/log/nginx/ott-backend-*.log"
echo ""

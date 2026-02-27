#!/bin/bash

# VPS Quick Deploy Script
# Run this on a fresh Ubuntu 22.04 LTS VPS to setup OTT Backend
# Usage: bash vps_deploy.sh

set -e

echo "🚀 OTT Backend VPS Deployment Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root"
    exit 1
fi

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

# VPS Specifications & Provider Recommendations

## 📊 Minimum VPS Specifications

### For Small-Scale Usage (1-10 videos/day)

```
CPU:        2 cores (minimum)
RAM:        2GB
Storage:    50GB SSD
Bandwidth:  200GB/month
Network:    1 Gbps unmetered
OS:         Ubuntu 20.04 LTS or Ubuntu 22.04 LTS
```

**Cost Range:** $5-15/month
**Example:** Linode 2GB, Vultr 2GB, DigitalOcean Standard

### For Medium-Scale Usage (10-50 videos/day)

```
CPU:        4 cores
RAM:        4GB
Storage:    100GB SSD
Bandwidth:  500GB/month
Network:    1 Gbps unmetered
OS:         Ubuntu 22.04 LTS
```

**Cost Range:** $20-40/month
**Example:** Linode 4GB, Vultr 4GB, Contabo VPS-M

### For Large-Scale Usage (50+ videos/day)

```
CPU:        8 cores
RAM:        8GB
Storage:    250GB SSD
Bandwidth:  1TB/month
Network:    1 Gbps unmetered
OS:         Ubuntu 22.04 LTS
```

**Cost Range:** $40-80/month
**Example:** Linode 8GB, Vultr 8GB, Hetzner CX41

---

## 🎯 Recommended VPS Providers (Low Cost + High Uptime)

### 1. **Contabo** ⭐ BEST VALUE
```
Uptime SLA:     99.9%
Price-to-specs: Best in market
Payment:        Monthly (no discount)

Pricing (2026):
- VPS-M:     €4.99/mo   (4 cores, 8GB RAM, 160GB SSD)
- VPS-L:     €9.99/mo   (8 cores, 16GB RAM, 320GB SSD)
- VPS-XL:    €19.99/mo  (10 cores, 24GB RAM, 640GB SSD)

Pros:
✅ Cheapest high-spec options
✅ Good uptime (99.9%)
✅ Unmetered bandwidth
✅ Instant setup
✅ Payment in EUR (good for international)

Cons:
⚠️ Customer support slower than others
⚠️ Network sometimes oversubscribed
⚠️ UI could be better

Link: https://contabo.com/
```

### 2. **Linode (Akamai)** ⭐ MOST RELIABLE
```
Uptime SLA:     99.9%
Price-to-specs: Good value
Payment:        Monthly/Yearly (5% discount yearly)

Pricing (2026):
- Linode 2GB:   $12/mo   (1 core, 2GB RAM, 50GB SSD)
- Linode 4GB:   $24/mo   (2 cores, 4GB RAM, 80GB SSD)
- Linode 8GB:   $48/mo   (4 cores, 8GB RAM, 160GB SSD)

Pros:
✅ Excellent uptime (99.9%+)
✅ Fast network (40 Gbps)
✅ Great documentation
✅ Reliable support
✅ Predictable pricing

Cons:
⚠️ More expensive than Contabo
⚠️ Slower CPU than competitors
⚠️ Smaller disk for the price

Link: https://www.linode.com/
```

### 3. **Vultr** ⭐ BALANCED
```
Uptime SLA:     99.99%
Price-to-specs: Excellent value
Payment:        Hourly/Monthly (20-30% discount monthly)

Pricing (2026):
- 1vCPU, 1GB: $2.50/mo  (if billed monthly)
- 2vCPU, 2GB: $6/mo     (if billed monthly)
- 4vCPU, 4GB: $12/mo    (if billed monthly)

Pros:
✅ 99.99% uptime SLA
✅ Very fast global network
✅ Hourly billing (pay only for what you use)
✅ Good performance
✅ Instant deployment

Cons:
⚠️ Higher pricing if monthly
⚠️ Smaller communities
⚠️ Support could be faster

Link: https://www.vultr.com/
```

### 4. **DigitalOcean** ⭐ EASE OF USE
```
Uptime SLA:     99.99%
Price-to-specs: Good but pricier
Payment:        Monthly only

Pricing (2026):
- Basic ($6/mo):      1 vCPU, 1GB RAM, 25GB SSD
- Standard ($12/mo):  1 vCPU, 2GB RAM, 50GB SSD
- Standard ($24/mo):  2 vCPU, 4GB RAM, 80GB SSD

Pros:
✅ 99.99% uptime
✅ Easiest to use
✅ Great documentation
✅ Perfect for beginners
✅ One-click app deployment

Cons:
⚠️ Most expensive option
⚠️ Limited customization
⚠️ Smallest disk sizes

Link: https://www.digitalocean.com/
```

### 5. **Hetzner** ⭐ PERFORMANCE
```
Uptime SLA:     99.9%
Price-to-specs: Best performance/price
Payment:        Monthly

Pricing (2026):
- CPX11:   €4.99/mo    (2 cores, 4GB RAM, 40GB SSD)
- CPX21:   €9.99/mo    (4 cores, 8GB RAM, 80GB SSD)
- CPX31:   €19.99/mo   (8 cores, 16GB RAM, 160GB SSD)

Pros:
✅ Best performance/price
✅ Very fast network
✅ Located in Europe
✅ Excellent support
✅ Transparent pricing

Cons:
⚠️ Limited global locations
⚠️ Pricing in EUR (currency fluctuation)
⚠️ German support (sometimes language barrier)

Link: https://www.hetzner.com/
```

---

## 💰 Cost Comparison Table (Monthly)

| Provider | 2 CPU / 2GB | 4 CPU / 4GB | 8 CPU / 8GB | Uptime |
|----------|-----------|-----------|-----------|--------|
| **Contabo** | €4.99 ($5.3) | €9.99 ($10.6) | €19.99 ($21.2) | 99.9% |
| **Vultr** | $6 | $12 | $24 | 99.99% |
| **DigitalOcean** | $12 | $24 | $48 | 99.99% |
| **Linode** | $12 | $24 | $48 | 99.9% |
| **Hetzner** | €4.99 ($5.3) | €9.99 ($10.6) | €19.99 ($21.2) | 99.9% |

---

## 🎬 Storage & Bandwidth Calculation

### Typical Video Encoding Output
```
1 video (1 hour, 1080p input):
├─ 480p @ 800k:   ~400 MB
├─ 720p @ 1400k:  ~700 MB
└─ Temp files:   ~1.5 GB
────────────────────────
Total per video:   ~700 MB (stored in R2)
Temp needed:      ~1.5 GB (delete after)
```

### VPS Disk Space Needed
```
OS + dependencies:        10 GB
PostgreSQL data:          10 GB
Temporary files (/tmp):   50 GB (IMPORTANT!)
Freedom margin:           10 GB
─────────────────────────────
Total needed:            ~80 GB minimum
Recommended:            100+ GB
```

### Bandwidth Usage Per Video
```
1 video (1 hour):
├─ Upload to R2:    ~700 MB
├─ 5 users streaming (2x):   ~7 GB
└─ User downloads:  Variable

VPS Upload bandwith:  ~1-2 GB per video
R2 → User:           Minimal (charged to R2, not VPS)
```

---

## 🏆 Recommended Setup (BEST VALUE)

### Option A: Ultra Budget ($5-6/month)
```
Provider:   Contabo or Hetzner
Specs:      2 CPU, 4GB RAM, 40-50GB SSD
Videos:     1-5 per day
Cost/mo:    €4.99 ($5-6)
Issues:     Small disk, may need upgrade after 50+ videos
```

### Option B: Balanced ($10/month)
```
Provider:   Contabo or Hetzner
Specs:      4 CPU, 8GB RAM, 160GB SSD
Videos:     10-30 per day
Cost/mo:    €9.99 ($10)
Best for:   Small platforms, growing
```

### Option C: Production Ready ($20/month)
```
Provider:   Contabo or Hetzner
Specs:      8 CPU, 16GB RAM, 320GB SSD
Videos:     30-50 per day
Cost/mo:    €19.99 ($20)
Best for:   Medium platforms, reliable
```

### Option D: High Performance ($40/month)
```
Provider:   Vultr or Hetzner
Specs:      8-10 CPU, 16GB+ RAM, 500GB SSD
Videos:     50+ per day
Cost/mo:    $40-50
Best for:   Large platforms, priority
```

---

## ⚡ Performance Tips for VPS

### 1. Choose SSD Only
```
❌ HDD storage:     300 IOPS, slow encoding
✅ SSD storage:     10,000+ IOPS, fast encoding
✅ NVMe storage:    100,000+ IOPS, fastest

For video encoding: NVMe > SSD > HDD
If available, always choose NVMe!
```

### 2. CPU Architecture
```
Performance per core:
- Ryzen 5000+:     Best (10-15% faster)
- Intel Xeon:      Good (baseline)
- Older CPUs:      Slow

For FFmpeg, single-core performance matters!
```

### 3. Network Bandwidth
```
Encoding speed depends on:
- Input file size/quality (more important)
- CPU cores (more is better)
- Network NOT CRITICAL (async)

Don't prioritize network, prioritize CPU+RAM
```

---

## 🌍 Geographic Considerations

### Best Data Centers by Region

**Asia/India:**
- Vultr Singapore: Fast, reliable
- Linode Singapore: Good uptime
- Contabo EU: Slightly slower but cheap

**Europe:**
- Hetzner (Germany): Cheapest, fastest
- Contabo (multiple EU locations): Good
- Vultr Amsterdam: Premium option

**USA:**
- Vultr (multiple locations): 99.99% uptime
- Linode (multiple locations): Reliable
- DigitalOcean (multiple locations): Beginner-friendly

**Global:**
- Vultr: 32+ locations
- Linode: 11+ locations
- Contabo: 4+ locations
- Hetzner: 3+ locations

---

## 🚀 Quick Start: Deploy on VPS

### Step 1: Create VPS
```bash
# Pick a provider from above
# Choose Ubuntu 22.04 LTS
# SSH into your server
ssh root@your-vps-ip
```

### Step 2: Initial Setup
```bash
# Update system
apt update && apt upgrade -y

# Install FFmpeg (CRITICAL!)
apt install -y ffmpeg

# Install PostgreSQL
apt install -y postgresql postgresql-contrib

# Install Python + dependencies
apt install -y python3.10 python3-pip python3-venv

# Create database
sudo -u postgres psql << EOF
CREATE DATABASE ott_backend;
CREATE USER django WITH PASSWORD 'your_password';
ALTER ROLE django SET client_encoding TO 'utf8';
ALTER ROLE django SET default_transaction_isolation TO 'read committed';
ALTER ROLE django SET default_transaction_deferrable TO off;
ALTER ROLE django SET default_transaction_read_committed TO on;
GRANT ALL PRIVILEGES ON DATABASE ott_backend TO django;
\q
EOF

# Create directories
mkdir -p /var/media
mkdir -p /var/log
mkdir -p /tmp/hls_videos
chmod 777 /tmp/hls_videos
```

### Step 3: Deploy Application
```bash
# Clone or upload your code
cd /opt
git clone your-repo
cd ott-backend

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r HLS_REQUIREMENTS.txt

# Configure .env
nano .env
# Add R2 credentials, DB password, secret key

# Migrations
python manage.py migrate
python manage.py createsuperuser

# Start with Gunicorn
pip install gunicorn
gunicorn --workers 4 --timeout 1800 --bind 0.0.0.0:8000 ott_backend.wsgi:application
```

### Step 4: Configure Nginx
```bash
# Install Nginx
apt install -y nginx

# Create config
cat > /etc/nginx/sites-available/ott-backend << 'EOF'
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    client_max_body_size 5G;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 1800s;
        proxy_connect_timeout 1800s;
        proxy_send_timeout 1800s;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/ott-backend /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 5: SSL (Let's Encrypt)
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

---

## 📈 Scaling Path

```
Phase 1: Start ($5-10/mo)
├─ 2-4 CPU, 2-4GB RAM
├─ 50GB SSD
├─ 1-10 videos/day
└─ Single VPS

Phase 2: Growth ($20-40/mo)
├─ 8 CPU, 8GB RAM
├─ 200GB SSD
├─ 20-50 videos/day
└─ Single VPS or load balanced

Phase 3: Scale ($50-100/mo)
├─ 10+ CPU, 16GB+ RAM
├─ 500GB+ SSD
├─ 50+ videos/day
└─ Multiple servers + load balancer
```

---

## 💡 Cost Breakdown (Annual)

### Small Platform Setup ($10/mo)
```
VPS (Contabo 4CPU/8GB):    €9.99/mo   = €119.88/year
R2 Storage (500 videos):    $15/mo     = $180/year
R2 Bandwidth:               $10/mo     = $120/year
PostgreSQL backups:         $5/mo      = $60/year
─────────────────────────────────────────
Total:                      ~$600/year
Per video:                  ~$1.20/year
```

### Medium Platform Setup ($25/mo)
```
VPS (Contabo 8CPU/16GB):    €19.99/mo  = €240/year
R2 Storage (2000 videos):   $40/mo     = $480/year
R2 Bandwidth:               $25/mo     = $300/year
PostgreSQL backups:         $10/mo     = $120/year
─────────────────────────────────────────
Total:                      ~$1,440/year
Per video:                  ~$0.72/year
```

---

## 🔒 Security Recommendations

```bash
# UFW Firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# SSH Hardening
# Disable root login
sed -i 's/^#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config

# Use SSH keys only
sed -i 's/^#PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

systemctl restart sshd

# Fail2Ban
apt install -y fail2ban
systemctl enable fail2ban
```

---

## 🆘 Troubleshooting VPS

### High CPU Usage During Encoding
```
✅ Normal: FFmpeg uses 80-100% during encoding
⚠️  If over 100% (multiple encodes): Upgrade CPU
```

### Disk Space Filling Up
```
# Check disk
df -h

# Clean temp
rm -rf /tmp/hls_videos/*

# Clean old PostgreSQL (if needed)
sudo -u postgres vacuum full;
```

### Out of Memory
```
# Check memory
free -h

# Monitor during encoding
watch -n 1 'free -h'

# If OOM: Upgrade RAM or reduce bitrate
```

---

## 📋 Final Recommendation

### Best All-Around: **Contabo VPS-M**
```
Price:        €4.99-9.99/month
Specs:        4 cores, 8GB RAM, 160GB SSD
Uptime:       99.9%
Bandwidth:    Unmetered
Best for:     Small to medium platforms

Link: https://contabo.com/
```

### Best Reliability: **Linode 4GB**
```
Price:        $24/month
Specs:        2 cores, 4GB RAM, 80GB SSD
Uptime:       99.9%+
Support:      Excellent
Best for:     Those who want peace of mind

Link: https://www.linode.com/
```

### Best Performance: **Hetzner CPX21**
```
Price:        €9.99/month
Specs:        4 cores, 8GB RAM, 80GB SSD (NVMe)
Uptime:       99.9%
Network:      40 Gbps
Best for:     Performance-critical platforms

Link: https://www.hetzner.com/
```

---

## CLI Command Cheat Sheet

```bash
# Check VPS stats
neofetch
htop
df -h
free -h

# Monitor encoding
ps aux | grep ffmpeg
tail -f /var/log/hls_streaming.log

# Check network
ping google.com
curl -I https://r2.cloudflarestorage.com

# PostgreSQL status
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"

# Nginx status
sudo systemctl status nginx
curl http://localhost:8000/admin/
```

Choose Contabo or Hetzner for best value! 🚀

# VPS Provider Detailed Comparison (2026)

## Direct Comparison Matrix

### By Price Tier

#### $5-6/Month (Ultra Budget)
```
🏆 WINNER: Contabo VPS-M
├─ CPU: 4 cores
├─ RAM: 8GB
├─ Storage: 160GB SSD
├─ Price: €4.99/mo
├─ Uptime: 99.9%
├─ Best for: Single video per day
└─ Link: https://contabo.com/

Alternatives:
- Hetzner CPX-11 (€4.99/mo): Similar specs
```

#### $10-12/Month (Small Business)
```
🏆 WINNER: Vultr (billed monthly)
├─ CPU: 4 vCPU
├─ RAM: 4GB
├─ Storage: 80GB SSD
├─ Price: $12/mo
├─ Uptime: 99.99%
├─ Best for: 10-20 videos/week
└─ Link: https://www.vultr.com/

Alternatives:
- Contabo VPS-M: Same specs, €4.99/mo (but slower support)
- Linode 4GB: $24/mo (more premium)
- DigitalOcean: $12/mo (but smaller disk)
```

#### $20-25/Month (Growing Business)
```
🏆 WINNER: Contabo VPS-L
├─ CPU: 8 cores
├─ RAM: 16GB
├─ Storage: 320GB SSD
├─ Price: €9.99/mo
├─ Uptime: 99.9%
├─ Best for: 30-50 videos/week
└─ Link: https://contabo.com/

Alternatives:
- Hetzner CPX-21 (€9.99/mo): Better performance
- Vultr 4vCPU/8GB ($24/mo): Better uptime
- Linode 8GB ($48/mo): Most reliable
```

#### $40-50/Month (Enterprise)
```
🏆 WINNER: Hetzner CPX-31
├─ CPU: 8 cores
├─ RAM: 16GB
├─ Storage: 160GB NVMe
├─ Price: €19.99/mo
├─ Uptime: 99.9%
├─ Best for: 50+ videos/week
└─ Link: https://www.hetzner.com/

Alternatives:
- Vultr 8vCPU/16GB ($40/mo): Better network
- Contabo VPS-XL (€19.99/mo): Similar
- Linode 16GB ($96/mo): Premium option
```

---

## Detailed Provider Profiles

### 1. Contabo ⭐ BUDGET CHAMPION

**Overview:**
- German company, founded 2003
- Focus: Best value, generous specs
- Locations: Germany, New York, Singapore

**Pros:**
```
✅ Best price-to-specs ratio on market
✅ Very generous RAM for price
✅ Unmetered bandwidth (truly unlimited)
✅ No hidden fees
✅ Instant activation (usually <5 minutes)
✅ User-friendly control panel
✅ Strong European presence
```

**Cons:**
```
⚠️ Support response slower (wait hours)
⚠️ Network sometimes oversold (peak hours slower)
⚠️ Control panel less polished than competitors
⚠️ Limited to 4 simultaneous tickets (paid tier)
⚠️ Data centers fewer than competitors
```

**Best For:**
```
- Budget-conscious startups
- Europeans (closest data centers)
- Those who don't need 24/7 support
- Medium-scale platforms (100-1000 videos)
```

**Pricing Example (2026):**
```
VPS-M:  4 cores, 8GB RAM, 160GB SSD = €4.99/mo
VPS-L:  8 cores, 16GB RAM, 320GB SSD = €9.99/mo
VPS-XL: 10 cores, 24GB RAM, 640GB SSD = €19.99/mo
```

**Link:** https://contabo.com/
**Rating:** 8.5/10 for our use case

---

### 2. Linode (Akamai) ⭐ RELIABILITY CHAMPION

**Overview:**
- Acquired by Akamai (2021)
- Focus: Reliability, performance, documentation
- Locations: 11 global data centers

**Pros:**
```
✅ Excellent uptime (99.9%+ proven track record)
✅ Fast network (40 Gbps, never throttled)
✅ Outstanding documentation (best in industry)
✅ Responsive support (24/7)
✅ Predictable pricing (no surprises)
✅ Good API for automation
```

**Cons:**
```
⚠️ More expensive than budget options
⚠️ Smaller disk per dollar compared to competitors
⚠️ Slower single-thread CPU than latest Ryzen
⚠️ Yearly discount only 5% (not much)
```

**Best For:**
```
- Production systems where reliability matters
- Companies that value support
- Those with budget flexibility
- Medium-to-large platforms
```

**Pricing Example (2026):**
```
Linode 2GB:  1 core, 2GB RAM, 50GB SSD = $12/mo
Linode 4GB:  2 cores, 4GB RAM, 80GB SSD = $24/mo
Linode 8GB:  4 cores, 8GB RAM, 160GB SSD = $48/mo
```

**Link:** https://www.linode.com/
**Rating:** 9/10 overall (best for production)

---

### 3. Vultr ⭐ PERFORMANCE CHAMPION

**Overview:**
- US company, founded 2014
- Focus: Performance, global presence, hourly billing
- Locations: 32+ data centers worldwide

**Pros:**
```
✅ 99.99% uptime (highest SLA)
✅ Fastest network globally (best peering)
✅ Hourly billing (pay only what you use)
✅ Instant deployment (seconds)
✅ Great API (automation-friendly)
✅ Generous free tier for testing
✅ Best for multi-region redundancy
```

**Cons:**
```
⚠️ Hourly billing expensive if forgot to shutdown
⚠️ Monthly pricing still pricey ($12/mo for 2GB)
⚠️ Smaller community than DigitalOcean
⚠️ No bundled "app templates" like DO
```

**Best For:**
```
- Global applications (many regions)
- Performance-critical apps
- Those who want to scale quickly
- High-traffic platforms
```

**Pricing Example (2026):**
```
1vCPU, 1GB:    $2.50/mo (if monthly)
2vCPU, 2GB:    $6.00/mo (if monthly)
4vCPU, 4GB:    $12.00/mo (if monthly)

Hourly: $0.0037/hour = ~$2.70/month (if $2.50/mo plan)
```

**Link:** https://www.vultr.com/
**Rating:** 9/10 (best performance)

---

### 4. DigitalOcean ⭐ BEGINNER CHAMPION

**Overview:**
- US company, founded 2011
- Focus: Ease of use, community, educational
- Locations: 8 global data centers

**Pros:**
```
✅ Easiest to use (perfect for beginners)
✅ 99.99% uptime SLA
✅ Excellent documentation
✅ Large community (lots of tutorials)
✅ One-click app deployments
✅ Free tier credits ($200 for new users)
✅ Integrated analytics and monitoring
```

**Cons:**
```
⚠️ Most expensive option
⚠️ Limited customization in UI
⚠️ Smaller disk spaces at same price
⚠️ No hourly billing (monthly only)
⚠️ Less control for advanced users
```

**Best For:**
```
- Beginners/developers learning
- Those who value ease over price
- Small projects with good uptime needs
- Users who want GUI over CLI
```

**Pricing Example (2026):**
```
Basic ($6/mo):     1 vCPU, 1GB RAM, 25GB SSD
Standard ($12/mo): 1 vCPU, 2GB RAM, 50GB SSD
Standard ($24/mo): 2 vCPU, 4GB RAM, 80GB SSD
```

**Link:** https://www.digitalocean.com/
**Rating:** 8/10 (excellent for beginners)

---

### 5. Hetzner ⭐ PERFORMANCE/VALUE CHAMPION

**Overview:**
- German company, established 1997
- Focus: Performance, value, European focus
- Locations: Germany, Finland, Germany (US expansion 2024+)

**Pros:**
```
✅ Best performance/price (newer hardware)
✅ Excellent support (German company, professional)
✅ Very fast network (best European uplink)
✅ NVMe storage standard (faster than SSD)
✅ Transparent pricing (no surprises)
✅ Dedicated server IP included
✅ Strong European presence
```

**Cons:**
```
⚠️ Limited global locations (mostly EU)
⚠️ Pricing in EUR (currency fluctuation risk)
⚠️ German-first company (some language barrier)
⚠️ Smaller global community
⚠️ No hourly billing
```

**Best For:**
```
- European users/servers
- Performance matters
- Those who want NVMe (not SSD)
- Companies wanting "German engineering"
```

**Pricing Example (2026):**
```
CPX-11: 2 cores, 4GB RAM, 40GB NVMe = €4.99/mo
CPX-21: 4 cores, 8GB RAM, 80GB NVMe = €9.99/mo
CPX-31: 8 cores, 16GB RAM, 160GB NVMe = €19.99/mo
```

**Link:** https://www.hetzner.com/
**Rating:** 9.5/10 (best value in Europe)

---

## Alternative Providers (If Main Options Full)

### OVH
```
Price:     €3.59/mo
Specs:     1 core, 2GB RAM, 20GB SSD
Uptime:    99.9%
Pros:      Cheapest, French company
Cons:      Slower CPU, small disk
Link:      https://www.ovh.com/
Rating:    7/10 (very budget, less reliable)
```

### Scaleway
```
Price:     €3.99/mo
Specs:     2 cores, 2GB RAM, 20GB SSD
Uptime:    99.95%
Pros:      Cheapest with good specs, ARM CPU
Cons:      ARM architecture (not x86), small disk
Link:      https://www.scaleway.com/
Rating:    6.5/10 (good for learning, not production)
```

### AWS EC2
```
Price:     $3.50/mo (t3.small, 1 year commitment)
Specs:     2 vCPU, 2GB RAM, 20GB EBS
Uptime:    99.99%
Pros:      Scaling, global CDN, enterprise
Cons:      Complex pricing, learning curve
Link:      https://aws.amazon.com/ec2/
Rating:    7/10 (overkill for this use case)
```

### Google Cloud
```
Price:     $8.50/mo (f1-micro, US)
Specs:     Shared CPU, 0.6GB RAM, 10GB SSD
Uptime:    99.95%
Pros:      Global cloud, enterprise grade
Cons:      Expensive for specs, complex
Link:      https://cloud.google.com/compute
Rating:    6/10 (overkill for this use case)
```

---

## My Top 3 Recommendations

### For Cost (Winner: Contabo)
```
Tier:       VPS-M
Price:      €4.99/month
Specs:      4 cores, 8GB RAM, 160GB SSD
Uptime:     99.9%
Good for:   Bootstrap startups, low budget
```

### For Reliability (Winner: Linode)
```
Tier:       Linode 4GB
Price:      $24/month
Specs:      2 cores, 4GB RAM, 80GB SSD
Uptime:     99.9%+
Good for:   Production, peace of mind
```

### For Balance (Winner: Hetzner)
```
Tier:       CPX-21
Price:      €9.99/month (≈$10.60)
Specs:      4 cores, 8GB RAM, 80GB NVMe
Uptime:     99.9%
Good for:   Best performance/price
```

---

## Deployment Timeline

### Choose Provider (Day 1)
```
1. Compare prices ← you are here
2. Pick: Contabo, Hetzner, or Linode
3. Create account (2 minutes)
```

### Order VPS (Day 1)
```
1. Login to provider
2. Choose region (Germany/EU/US)
3. Choose Ubuntu 22.04 LTS
4. Click "Create"
5. Receive login credentials (email, 5-60 minutes)
```

### Initial Setup (Day 1-2)
```
1. SSH into VPS: ssh root@IP
2. Run: bash vps_deploy.sh
3. Configure: nano .env
4. Takes: 30 minutes total
```

### Deploy App (Day 2)
```
1. Upload your OTT Backend code
2. Run migrations
3. Start service
4. Configure domain + SSL
5. Takes: 1-2 hours
```

### Go Live (Day 2)
```
1. Point domain to VPS IP
2. Test upload API
3. Monitor logs
4. Done!
```

---

## Provider Switch Migration

If you ever need to switch from one provider to another:

```
0. Backup everything
   - Database: pg_dump
   - Files: tar of /opt/ott-backend
   - R2: No need (independent)

1. Setup new VPS with same specs
   - Run vps_deploy.sh
   - Install dependencies

2. Transfer application
   - scp files from old to new
   - Or git push/pull

3. Migrate database
   - pg_dump from old
   - psql restore to new
   - Or export/import

4. Update DNS
   - Point to new IP
   - Wait for TTL

5. Verify everything works
   - Test uploads
   - Check R2 uploads
   - Monitor logs

Time: 2-3 hours, Zero downtime (with DNS cutover)
```

---

## Final Verdict

| Situation | Recommendation | Price |
|-----------|----------------|-------|
| **Startup** | Contabo VPS-M | €4.99/mo |
| **Small Business** | Hetzner CPX-21 | €9.99/mo |
| **Production** | Linode 4GB | $24/mo |
| **Global** | Vultr 2vCPU | $6/mo |
| **Enterprise** | Linode 8GB | $48/mo |

**My personal choice if building this:** Hetzner CPX-21 (€9.99/mo)
- Best performance/price balance
- Excellent support
- NVMe faster than SSD
- Located in Europe (good for most users)

---

## Next Steps

1. ✅ Read VPS_SPECIFICATIONS.md (complete guide)
2. ✅ Pick a provider from above
3. ✅ Create account + order VPS
4. ✅ Download vps_deploy.sh
5. ✅ SSH into VPS
6. ✅ Run: `bash vps_deploy.sh`
7. ✅ Upload your OTT Backend code
8. ✅ Configure .env with R2 credentials
9. ✅ Run migrations
10. ✅ Start service: `systemctl start ott-backend`
11. ✅ Configure domain + SSL
12. ✅ Monitor logs: `tail -f /var/log/hls_streaming.log`
13. ✅ Test upload API
14. ✅ Launch! 🚀

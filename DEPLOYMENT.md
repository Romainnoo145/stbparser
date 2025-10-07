# STB Sync Server - Deployment Guide

**Huidige Status:** Draait lokaal met localtunnel
**Doel:** 24/7 productie server zonder manuele interventie

---

## Productie Requirements

### Wat je nodig hebt:
1. ✅ **Ubuntu server** met publiek IP adres
2. ✅ **Redis** voor background job processing
3. ✅ **Python 3.10+** environment
4. ✅ **Nginx** (optioneel, voor SSL/reverse proxy)
5. ✅ **Systemd services** voor auto-restart
6. ✅ **SSL certificaat** (gratis via Let's Encrypt)

### Wat de server doet:
- Ontvangt webhooks van Offorte 24/7
- Verwerkt proposals in achtergrond (Redis queue)
- Synct naar Airtable (8 tabellen)
- Auto-restart bij crashes
- Logging voor debugging

---

## Optie 1: DigitalOcean Droplet (AANBEVOLEN)

**Kosten:** €6/maand (Basic Droplet)
**Setup tijd:** ~30 minuten
**Moeilijkheidsgraad:** ⭐⭐ Gemiddeld

### Stap 1: Droplet aanmaken

```bash
# Via DigitalOcean dashboard:
1. Create Droplet
2. Kies Ubuntu 22.04 LTS
3. Kies Basic plan (€6/maand, 1GB RAM)
4. Kies datacenter: Amsterdam
5. Add SSH key (of wachtwoord)
6. Create Droplet

# Je krijgt een publiek IP: bijv. 143.198.123.45
```

### Stap 2: Server setup

```bash
# SSH naar je server
ssh root@143.198.123.45

# Update systeem
apt update && apt upgrade -y

# Installeer dependencies
apt install -y python3 python3-pip python3-venv redis-server nginx certbot python3-certbot-nginx git

# Start Redis
systemctl start redis-server
systemctl enable redis-server

# Check Redis
redis-cli ping
# Should return: PONG
```

### Stap 3: Deploy applicatie

```bash
# Clone je repository (of upload via scp/rsync)
cd /opt
git clone <your-repo-url> stbparser
cd stbparser

# Maak virtual environment
python3 -m venv venv
source venv/bin/activate

# Installeer dependencies
pip install -r requirements.txt

# Maak .env file
nano .env
# Vul in:
# OFFORTE_API_KEY=your_offorte_api_key_here
# OFFORTE_ACCOUNT_NAME=stb-kozijnen
# AIRTABLE_API_KEY=your_airtable_api_key_here
# AIRTABLE_BASE_STB_SALES=app9mz6mT0zk8XRGm
# AIRTABLE_BASE_STB_ADMINISTRATIE=appuXCPmvIwowH78k
# REDIS_URL=redis://localhost:6379/0
# SERVER_PORT=8002
```

### Stap 4: Systemd Services (Auto-restart)

**FastAPI Server service:**

```bash
nano /etc/systemd/system/stb-api.service
```

```ini
[Unit]
Description=STB Offorte-Airtable Sync API
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stbparser
Environment="PATH=/opt/stbparser/venv/bin"
ExecStart=/opt/stbparser/venv/bin/python3 -m backend.api.server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Redis Worker service:**

```bash
nano /etc/systemd/system/stb-worker.service
```

```ini
[Unit]
Description=STB Redis Worker for Proposal Sync
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stbparser
Environment="PATH=/opt/stbparser/venv/bin"
ExecStart=/opt/stbparser/venv/bin/python3 -m backend.workers.proposal_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Start services:**

```bash
# Reload systemd
systemctl daemon-reload

# Start services
systemctl start stb-api
systemctl start stb-worker

# Enable auto-start on boot
systemctl enable stb-api
systemctl enable stb-worker

# Check status
systemctl status stb-api
systemctl status stb-worker

# View logs
journalctl -u stb-api -f
journalctl -u stb-worker -f
```

### Stap 5: Nginx Reverse Proxy + SSL

```bash
# Nginx config
nano /etc/nginx/sites-available/stb-sync
```

```nginx
server {
    listen 80;
    server_name stb-sync.jouwdomein.nl;  # Of gebruik IP adres

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Activeer site
ln -s /etc/nginx/sites-available/stb-sync /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx

# SSL certificaat (gratis, automatisch vernieuwen)
certbot --nginx -d stb-sync.jouwdomein.nl

# Test SSL renewal
certbot renew --dry-run
```

### Stap 6: Update Offorte Webhook

```bash
# Je webhook URL is nu:
https://stb-sync.jouwdomein.nl/webhook/offorte

# Of zonder domeinnaam:
http://143.198.123.45/webhook/offorte
```

Update in Offorte dashboard of via script:

```bash
cd /opt/stbparser
source venv/bin/activate
PYTHONPATH=. python3 scripts/register_offorte_webhook.py https://stb-sync.jouwdomein.nl/webhook/offorte
```

### Stap 7: Testen

```bash
# Test of API draait
curl http://localhost:8002/health

# Test webhook endpoint
curl -X POST http://localhost:8002/webhook/offorte \
  -H "Content-Type: application/json" \
  -d '{"event": "test"}'

# Check logs
journalctl -u stb-api -n 50
journalctl -u stb-worker -n 50
```

**✅ Klaar! Server draait nu 24/7**

---

## Optie 2: Railway.app (MAKKELIJKST)

**Kosten:** ~€5-10/maand
**Setup tijd:** ~15 minuten
**Moeilijkheidsgraad:** ⭐ Makkelijk (no-code deployment)

### Voordelen:
- ✅ Geen server management
- ✅ Automatische HTTPS
- ✅ Redis addon met 1 klik
- ✅ Git push = auto deploy
- ✅ Logs via dashboard
- ✅ Gratis trial ($5 credit)

### Setup:

1. **Account aanmaken**
   - Ga naar https://railway.app
   - Sign up met GitHub

2. **New Project**
   - Click "New Project"
   - Click "Deploy from GitHub repo"
   - Selecteer je stbparser repo

3. **Environment Variables**
   - Ga naar Settings → Variables
   - Voeg toe:
     ```
     OFFORTE_API_KEY=your_offorte_api_key_here
     OFFORTE_ACCOUNT_NAME=stb-kozijnen
     AIRTABLE_API_KEY=your_airtable_api_key_here
     AIRTABLE_BASE_STB_SALES=app9mz6mT0zk8XRGm
     AIRTABLE_BASE_STB_ADMINISTRATIE=appuXCPmvIwowH78k
     SERVER_PORT=8002
     ```

4. **Add Redis**
   - Click "New" → "Database" → "Add Redis"
   - Kopieer `REDIS_URL` naar environment variables

5. **Deploy**
   - Railway detecteert automatisch Python
   - Voeg `Procfile` toe aan je repo:
     ```
     web: python3 -m backend.api.server
     worker: python3 -m backend.workers.proposal_worker
     ```
   - Push naar GitHub → automatische deploy

6. **Get Public URL**
   - Ga naar Settings → Networking
   - Click "Generate Domain"
   - Je krijgt: `stbparser-production.up.railway.app`

7. **Update Webhook**
   ```bash
   PYTHONPATH=. python3 scripts/register_offorte_webhook.py \
     https://stbparser-production.up.railway.app/webhook/offorte
   ```

**✅ Klaar! Railway handelt alles af**

---

## Optie 3: Hetzner Cloud (GOEDKOOPST)

**Kosten:** €4/maand
**Setup:** Identiek aan DigitalOcean
**Voordeel:** EU data centers, AVG-compliant, goedkoper

### Setup:
1. Account op https://www.hetzner.com/cloud
2. Create Server → Ubuntu 22.04 → CX11 (€4/maand)
3. Volg exact dezelfde stappen als DigitalOcean hierboven

---

## Monitoring & Maintenance

### Health Check Endpoint

Je API heeft nu `/health` endpoint:

```bash
curl https://stb-sync.jouwdomein.nl/health
# Returns: {"status": "healthy", "timestamp": "..."}
```

### UptimeRobot (Gratis Monitoring)

1. Ga naar https://uptimerobot.com
2. Add New Monitor
3. Monitor Type: HTTP(s)
4. URL: `https://stb-sync.jouwdomein.nl/health`
5. Monitoring Interval: 5 minuten
6. Alert Contacts: je email

**Als server down gaat → je krijgt email binnen 5 minuten**

### Log Rotatie (voorkom volle disk)

```bash
nano /etc/logrotate.d/stb-sync
```

```
/opt/stbparser/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    missingok
}
```

### Backup Script (Optioneel)

```bash
nano /opt/stbparser/backup.sh
```

```bash
#!/bin/bash
# Backup environment variables
cp /opt/stbparser/.env /opt/stbparser/backups/.env.$(date +%Y%m%d)

# Cleanup old backups (keep last 30 days)
find /opt/stbparser/backups -name ".env.*" -mtime +30 -delete
```

```bash
chmod +x /opt/stbparser/backup.sh

# Daily cron
crontab -e
# Add:
0 3 * * * /opt/stbparser/backup.sh
```

---

## Update Workflow

### Code updates via Git:

```bash
ssh root@143.198.123.45
cd /opt/stbparser

# Pull latest code
git pull origin main

# Restart services
systemctl restart stb-api
systemctl restart stb-worker

# Check logs
journalctl -u stb-api -n 50 -f
```

### Automatische updates (optioneel):

```bash
nano /opt/stbparser/update.sh
```

```bash
#!/bin/bash
cd /opt/stbparser
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
systemctl restart stb-api
systemctl restart stb-worker
```

```bash
chmod +x /opt/stbparser/update.sh

# Weekly auto-update (zondag 2am)
crontab -e
# Add:
0 2 * * 0 /opt/stbparser/update.sh
```

---

## Kosten Vergelijking

| Platform | Kosten/maand | Setup | Management | SSL | Redis |
|----------|--------------|-------|------------|-----|-------|
| **DigitalOcean** | €6 | Medium | Manual | Manual (gratis) | Manual install |
| **Railway** | €5-10 | Easy | Auto | Auto (gratis) | 1-click addon |
| **Hetzner** | €4 | Medium | Manual | Manual (gratis) | Manual install |
| **Lokaal (nu)** | €0 | Easy | Manual | ❌ Geen | Lokaal |

---

## Mijn Aanbeveling

**Voor STB zou ik kiezen voor:**

### **DigitalOcean Droplet**
- ✅ €6/maand = €72/jaar (zeer betaalbaar)
- ✅ Volledige controle
- ✅ Makkelijk te beheren met systemd
- ✅ Nederlandse datacenter (Amsterdam)
- ✅ Schaalbaar als je later meer nodig hebt

**Waarom niet Railway?**
- Duurder op lange termijn
- Minder controle over server
- Vendor lock-in

**Setup tijd:** 30-45 minuten eenmalig, daarna onderhoudsvrij

---

## Next Steps

Wil je dat ik:
1. ✅ **Een deployment script maak** voor automatische DigitalOcean setup?
2. ✅ **Railway.app Procfile** toevoegen voor one-click deploy?
3. ✅ **Docker container** maken voor nog makkelijkere deployment?
4. ✅ **Monitoring dashboard** toevoegen aan de API?

Laat me weten welke hosting optie je wilt en ik help je met de deployment! 🚀

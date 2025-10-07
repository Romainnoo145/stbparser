# Coolify + Cloudflare Deployment Guide

**Stack:** Coolify (self-hosted PaaS) + Cloudflare Tunnel + Docker Compose

---

## Prerequisites

1. ✅ **Coolify server** (je eigen VPS met Coolify geïnstalleerd)
2. ✅ **Cloudflare account** met domein toegevoegd
3. ✅ **GitHub repo** met code (https://github.com/Romainnoo145/stbparser)

---

## Architecture

```
Offorte Webhook
    ↓
Cloudflare Tunnel (SSL + DDoS protection)
    ↓
Coolify Server (je VPS)
    ↓
Docker Compose:
  - api (FastAPI webhook receiver)
  - worker (Redis queue processor)
  - redis (job queue)
    ↓
Airtable (8 tabellen sync)
```

---

## Step 1: Coolify Setup

1. Login naar Coolify dashboard
2. New Project → Docker Compose
3. Connect GitHub: `Romainnoo145/stbparser`
4. Branch: `main`
5. Auto-deploy: enabled

---

## Step 2: Environment Variables in Coolify

```bash
OFFORTE_API_KEY=your_offorte_api_key_here
OFFORTE_ACCOUNT_NAME=stb-kozijnen
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_STB_SALES=app9mz6mT0zk8XRGm
AIRTABLE_BASE_STB_ADMINISTRATIE=appuXCPmvIwowH78k
REDIS_URL=redis://redis:6379/0
SERVER_PORT=8002
```

---

## Step 3: Deploy

1. Click "Deploy" in Coolify
2. Wait for build (~2-3 min)
3. Check logs for errors

---

## Step 4: Cloudflare Tunnel

1. Coolify → Networking → Enable Cloudflare Tunnel
2. Domain: `stb-sync.jouwdomein.nl`
3. Coolify configures automatically

---

## Step 5: Update Offorte Webhook

```bash
# Update webhook URL
PYTHONPATH=. python3 scripts/register_offorte_webhook.py https://stb-sync.jouwdomein.nl/webhook/offorte
```

---

## Done! 🎉

Server now runs 24/7:
- Auto-restart on crash
- Auto-deploy on git push
- SSL via Cloudflare
- Health monitoring

**Cost:** €4-10/month for VPS

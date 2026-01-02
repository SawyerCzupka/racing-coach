# LapEvo Marketing Site - Deployment Options

This document outlines deployment options for the LapEvo marketing site that align with a FOSS-first, cost-effective approach.

## Current Setup (Docker Compose)

For local development and simple self-hosted deployments:

```bash
# Development (hot reload)
docker compose up lapevo-marketing

# Production (static build)
docker compose -f docker-compose.prod.yaml up lapevo-marketing
```

The site will be available at:
- Development: http://localhost:4321
- Production: http://localhost:4321

---

## Deployment Options

### 1. Self-Hosted VPS (Recommended for Control)

**Cost**: ~$5-20/month depending on provider

**Options**:
- **Hetzner Cloud** - Excellent price/performance, EU-based
- **DigitalOcean** - Simple, good documentation
- **Linode** - Reliable, good support
- **Vultr** - Competitive pricing

**Setup**:
1. Provision a VPS with Docker installed
2. Clone the repo and run `docker compose -f docker-compose.prod.yaml up -d`
3. Set up a reverse proxy (Caddy recommended - auto SSL)

**Example Caddy config**:
```
lapevo.com {
    reverse_proxy lapevo-marketing:80
}

app.lapevo.com {
    reverse_proxy racing-coach-web:80
}

api.lapevo.com {
    reverse_proxy racing-coach-server:8000
}
```

---

### 2. Coolify (FOSS PaaS - Self-Hosted)

**Cost**: Free (self-hosted) + VPS cost

Coolify is an open-source, self-hostable Heroku/Vercel alternative.

**Setup**:
1. Install Coolify on a VPS: https://coolify.io/docs/installation
2. Connect your GitHub repo
3. Configure build settings:
   - Build command: `npm run build`
   - Output directory: `dist`
   - Dockerfile: Use existing

**Pros**:
- Full control, no vendor lock-in
- Automatic deployments from git
- Built-in SSL via Let's Encrypt
- Nice UI for managing deployments

---

### 3. Dokku (FOSS Heroku Alternative)

**Cost**: Free (self-hosted) + VPS cost

**Setup**:
```bash
# On your VPS
wget https://dokku.com/install/v0.34.0/bootstrap.sh
sudo DOKKU_TAG=v0.34.0 bash bootstrap.sh

# Create app
dokku apps:create lapevo-marketing

# Deploy
git remote add dokku dokku@your-server:lapevo-marketing
git push dokku main
```

---

### 4. Cloudflare Pages

**Cost**: Free tier is generous (500 builds/month, unlimited bandwidth)

**Setup**:
1. Connect GitHub repo to Cloudflare Pages
2. Configure build:
   - Build command: `npm run build`
   - Build output directory: `dist`
3. Set environment variable: `PUBLIC_API_URL=https://api.lapevo.com`

**Pros**:
- Extremely fast global CDN
- Free SSL
- Automatic deployments
- Edge caching

**Cons**:
- Not fully self-hosted
- Limited to static sites (which Astro produces)

---

### 5. Manual Nginx on VPS

For maximum control, deploy manually:

```bash
# Build locally
npm run build

# Upload to server
rsync -avz dist/ user@server:/var/www/lapevo-marketing/

# Nginx config
server {
    listen 80;
    server_name lapevo.com;
    root /var/www/lapevo-marketing;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Use Certbot for SSL: `sudo certbot --nginx -d lapevo.com`

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PUBLIC_API_URL` | API server URL for waitlist form | `http://localhost:8000` |

---

## Recommended Stack

For a solo developer or small team:

1. **VPS**: Hetzner CX22 (~$5/month) or similar
2. **Deployment**: Coolify (easiest) or Docker Compose + Caddy
3. **CDN** (optional): Cloudflare free tier in front
4. **Monitoring**: Uptime Kuma (FOSS, self-hosted)

This gives you full control, low cost, and no vendor lock-in.

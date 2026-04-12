# Deployment Guide

This guide covers deploying Alethian V2 to a production Linux server with Docker, Nginx reverse proxy, and systemd services.

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Server Setup](#server-setup)
- [Infrastructure Deployment](#infrastructure-deployment)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Nginx Configuration](#nginx-configuration)
- [SSL/TLS with Let's Encrypt](#ssltls-with-lets-encrypt)
- [Systemd Services](#systemd-services)
- [DGX Server Deployment](#dgx-server-deployment)
- [Environment Hardening](#environment-hardening)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Backup & Recovery](#backup--recovery)

---

## System Requirements

| Component | Minimum | Recommended |
|:----------|:--------|:------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 50 GB SSD | 200 GB SSD |
| GPU | Not required | NVIDIA GPU (for larger models) |
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

### Software Prerequisites

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Python 3.10+
sudo apt install python3 python3-venv python3-pip

# Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# Nginx
sudo apt install nginx certbot python3-certbot-nginx
```

---

## Server Setup

### 1. Create Application User

```bash
sudo useradd -m -s /bin/bash alethian
sudo usermod -aG docker alethian
sudo su - alethian
```

### 2. Clone Repository

```bash
cd /home/alethian
git clone <repository-url> Alethian
cd Alethian
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with **production** values:

```env
# Database — use strong passwords
POSTGRES_USER=alethian_prod
POSTGRES_PASSWORD=$(openssl rand -hex 24)
POSTGRES_DB=alethian_production

# Security — MUST change
JWT_SECRET=$(openssl rand -hex 32)
ALLOW_AUTO_REGISTRATION=False    # ← CRITICAL: disable in production

# Serper API
SERPER_API_KEY=your_real_key_here

# Service hosts (Docker internal names)
POSTGRES_HOST=postgres
REDIS_HOST=redis
QDRANT_HOST=qdrant
GROBID_URL=http://grobid:8070
```

> ⚠️ **CRITICAL:** Set `ALLOW_AUTO_REGISTRATION=False` in production to prevent unauthorized account creation.

---

## Infrastructure Deployment

### Start Services

```bash
cd infrastructure
docker compose up -d
```

### Verify All Services

```bash
# PostgreSQL
docker exec alethian_postgres pg_isready -U alethian_prod
# → accepting connections

# Redis
docker exec alethian_redis redis-cli ping
# → PONG

# Qdrant
curl -s http://localhost:6333/collections | python3 -m json.tool
# → {"result": {"collections": [...]}}

# Grobid (takes ~30s to start)
curl -s http://localhost:8070/api/isalive
# → true
```

### Data Persistence

Docker volumes store data across restarts:
- `postgres_data` → `/var/lib/docker/volumes/infrastructure_postgres_data/`
- `redis_data` → `/var/lib/docker/volumes/infrastructure_redis_data/`
- `qdrant_data` → `/var/lib/docker/volumes/infrastructure_qdrant_data/`

---

## Backend Deployment

### Install Dependencies

```bash
cd /home/alethian/Alethian/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### Initialize Database

```bash
# Create tables (runs automatically on first start via lifespan handler)
PYTHONPATH=. python -c "
from app.db.models import Base
from app.db.session import engine
Base.metadata.create_all(bind=engine)
print('Tables created successfully')
"
```

### Create Admin User

```bash
PYTHONPATH=. python -c "
from app.db.session import SessionLocal
from app.db.models import User, UserRole
from passlib.context import CryptContext
import os

pwd = CryptContext(schemes=['bcrypt'])
db = SessionLocal()

admin = User(
    username=os.getenv('ADMIN_EMAIL', 'admin@university.edu'),
    email=os.getenv('ADMIN_EMAIL', 'admin@university.edu'),
    hashed_password=pwd.hash(os.getenv('ADMIN_PASSWORD', 'change-me')),
    full_name='System Admin',
    role=UserRole.admin
)
db.add(admin)
db.commit()
print(f'Admin user created: {admin.username}')
db.close()
"
```

### Seed Document Archive (Optional)

If you have PDFs to pre-index:

```bash
PYTHONPATH=. python tests/seed_archive.py --archive-path /path/to/pdfs
```

### Start with Gunicorn

```bash
PYTHONPATH=. gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/alethian/access.log \
  --error-logfile /var/log/alethian/error.log
```

### Start Celery Worker

```bash
PYTHONPATH=. celery -A celery_worker worker \
  --loglevel=info \
  --concurrency=2 \
  --logfile=/var/log/alethian/celery.log
```

---

## Frontend Deployment

### Build Production Bundle

```bash
cd /home/alethian/Alethian/frontend

# Update API base URL for production
# Edit src/api/client.js:
#   baseURL: 'https://your-domain.edu/api/v1'

npm ci
npm run build
# → Output in dist/
```

### Serve via Nginx

The `dist/` directory contains static files served directly by Nginx (see next section).

---

## Nginx Configuration

```nginx
# /etc/nginx/sites-available/alethian
server {
    listen 80;
    server_name alethian.university.edu;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name alethian.university.edu;

    # SSL certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/alethian.university.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/alethian.university.edu/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend (React SPA)
    root /home/alethian/Alethian/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # File upload size
        client_max_body_size 100M;
    }

    # WebSocket proxy
    location /api/v1/documents/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/alethian /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/TLS with Let's Encrypt

```bash
sudo certbot --nginx -d alethian.university.edu
# Follow prompts — auto-renewal is configured
```

---

## Systemd Services

### Backend API Service

```ini
# /etc/systemd/system/alethian-api.service
[Unit]
Description=Alethian API Server
After=network.target docker.service
Requires=docker.service

[Service]
Type=exec
User=alethian
Group=alethian
WorkingDirectory=/home/alethian/Alethian/backend
Environment=PYTHONPATH=/home/alethian/Alethian/backend
ExecStart=/home/alethian/Alethian/backend/venv/bin/gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Celery Worker Service

```ini
# /etc/systemd/system/alethian-worker.service
[Unit]
Description=Alethian Celery Worker
After=network.target docker.service alethian-api.service
Requires=docker.service

[Service]
Type=exec
User=alethian
Group=alethian
WorkingDirectory=/home/alethian/Alethian/backend
Environment=PYTHONPATH=/home/alethian/Alethian/backend
ExecStart=/home/alethian/Alethian/backend/venv/bin/celery -A celery_worker worker \
    --loglevel=info \
    --concurrency=2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable & Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable alethian-api alethian-worker
sudo systemctl start alethian-api alethian-worker

# Check status
sudo systemctl status alethian-api
sudo systemctl status alethian-worker

# View logs
sudo journalctl -u alethian-api -f
sudo journalctl -u alethian-worker -f
```

---

## DGX Server Deployment

For GPU-accelerated processing on an NVIDIA DGX server:

### SSH Setup

```bash
ssh dgx-direct
cd ~/crawler_stuff/Downloads  # Archive documents location
```

### Key Differences

| Setting | Local | DGX |
|:--------|:------|:----|
| Archive path | `./Alethian_documents/` | `~/crawler_stuff/Downloads/` |
| SentenceTransformer | CPU | GPU (auto-detected) |
| Celery concurrency | 2 | 4-8 |

### Running Tests on DGX

```bash
ARCHIVE_PATH=~/crawler_stuff/Downloads MOCK_SERPER=true bash run_full_tests.sh
```

### GPU Model Loading

SentenceTransformer auto-detects GPU via PyTorch. No code changes needed — just ensure CUDA drivers are installed:

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## Environment Hardening

### Production Checklist

- [ ] `JWT_SECRET` — Unique random string (`openssl rand -hex 32`)
- [ ] `ALLOW_AUTO_REGISTRATION=False` — Prevent unauthorized signups
- [ ] `POSTGRES_PASSWORD` — Strong, unique password
- [ ] Remove `.env.example` from production server
- [ ] Configure firewall — only expose ports 80/443
- [ ] Block direct access to internal ports (5433, 6333, 6379, 8070)
- [ ] Enable HTTPS only (HTTP redirects to HTTPS)
- [ ] Set `CORS` origins to production domain only in `main.py`
- [ ] Regular security updates: `docker compose pull && docker compose up -d`

### Firewall Rules

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# API health
curl https://alethian.university.edu/

# Docker services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Disk usage
docker system df
du -sh /var/lib/docker/volumes/infrastructure_*
```

### Log Rotation

```bash
# /etc/logrotate.d/alethian
/var/log/alethian/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    create 0640 alethian alethian
}
```

### Update Procedure

```bash
cd /home/alethian/Alethian
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart alethian-api alethian-worker

# Frontend
cd ../frontend
npm ci
npm run build
# Nginx serves the new dist/ automatically

# Infrastructure (if docker-compose.yml changed)
cd ../infrastructure
docker compose pull
docker compose up -d
```

---

## Backup & Recovery

### Database Backup

```bash
# Automated daily backup
docker exec alethian_postgres pg_dump -U alethian_prod alethian_production | \
  gzip > /backups/alethian_$(date +%Y%m%d).sql.gz
```

### Qdrant Backup

```bash
# Snapshot entire Qdrant storage
docker run --rm -v infrastructure_qdrant_data:/data -v /backups:/backup \
  alpine tar czf /backup/qdrant_$(date +%Y%m%d).tar.gz /data
```

### Recovery

```bash
# Restore Postgres
gunzip -c /backups/alethian_20260409.sql.gz | \
  docker exec -i alethian_postgres psql -U alethian_prod alethian_production

# Restore Qdrant
docker compose stop qdrant
docker run --rm -v infrastructure_qdrant_data:/data -v /backups:/backup \
  alpine tar xzf /backup/qdrant_20260409.tar.gz -C /
docker compose start qdrant
```

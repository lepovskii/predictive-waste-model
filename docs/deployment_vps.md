# VPS Staging Deployment

_Target OS: Ubuntu 24.04_

## Goal

Run the full staging stack on one VPS:

```text
Frontend Next.js -> FastAPI -> PostgreSQL
                            -> Redis -> Celery Worker
```

Only the frontend is exposed publicly on port `80`.

Internal services:

```text
FastAPI: internal Docker network, plus localhost-only port 8000 for server debugging
PostgreSQL: internal Docker network only
Redis: internal Docker network only
```

---

## 1. Install Docker on VPS

Use Docker's official Ubuntu apt repository method.

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run hello-world
```

Optional, so the current user can run Docker without `sudo`:

```bash
sudo usermod -aG docker $USER
```

Then log out and log in again.

---

## 2. Clone Project

```bash
cd ~
git clone https://github.com/lepovskii/predictive-waste-model.git
cd predictive-waste-model
git checkout staging-vps
```

If the repository is private, configure GitHub authentication first.

---

## 3. Create Server Environment File

```bash
cp .env.staging.example .env.staging
nano .env.staging
```

Change at least:

```text
POSTGRES_PASSWORD
SECRET_KEY
```

Do not commit `.env.staging`.

---

## 4. Build Images

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml build
```

---

## 5. Start Database and Redis

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml up -d postgres redis
```

Check:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml ps
```

---

## 6. Run Database Migration

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml run --rm api alembic upgrade head
```

---

## 7. Start Full Stack

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml up -d
```

Check:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml ps
docker compose --env-file .env.staging -f docker-compose.staging.yml logs -f api
docker compose --env-file .env.staging -f docker-compose.staging.yml logs -f worker
```

---

## 8. Smoke Test

From inside the VPS:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1
```

From browser:

```text
http://PUBLIC_IP
```

Expected:

```text
Next.js frontend opens
CSV upload works
Prediction task reaches DRAFT
Prediction detail opens
Reconciliation works
```

---

## 9. Useful Commands

Restart stack:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml restart
```

Stop stack:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml down
```

View logs:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml logs -f
```

Rebuild after code update:

```bash
git pull
docker compose --env-file .env.staging -f docker-compose.staging.yml build
docker compose --env-file .env.staging -f docker-compose.staging.yml up -d
```

---

## Notes

This staging setup intentionally avoids exposing PostgreSQL and Redis to the public internet.

HTTPS/domain setup can be added later with Caddy, Nginx, or a cloud reverse proxy.

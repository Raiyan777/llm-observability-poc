# 🔧 Deployment Reference

> Step-by-step instructions for deploying and managing the Langfuse
> infrastructure and the `company-ai` SDK.

---

## EC2 Setup (One-time)

```bash
# 1. Launch EC2 (t3.medium, 30GB EBS, Amazon Linux 2023)

# 2. Install Docker
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker ec2-user

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Create project dir
sudo mkdir -p /opt/langfuse && cd /opt/langfuse
```

---

## Docker Compose

Copy the `docker-compose.yml` from this repo to `/opt/langfuse/` on EC2.

Key environment variables in the server `.env`:

```dotenv
# Postgres
POSTGRES_PASSWORD=<strong-random-password>

# Langfuse
NEXTAUTH_SECRET=<random-32-char-string>
ENCRYPTION_KEY=<random-64-hex-chars>
NEXTAUTH_URL=http://<ec2-ip>:3000
LANGFUSE_INIT_ORG_NAME=your-company
LANGFUSE_INIT_PROJECT_NAME=llm-observability
LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-lf-...
LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-lf-...
LANGFUSE_INIT_USER_EMAIL=admin@company.com
LANGFUSE_INIT_USER_PASSWORD=<admin-password>
```

```bash
# Start
docker compose up -d

# Verify
curl http://localhost:3000/api/public/health
```

---

## Backup & Restore

### Backup

```bash
# Postgres
docker compose exec postgres pg_dump -U postgres langfuse > /backups/langfuse_$(date +%Y%m%d).sql

# Full volume backup (nuclear option)
docker compose down
tar czf /backups/langfuse_volumes_$(date +%Y%m%d).tar.gz /var/lib/docker/volumes/
docker compose up -d
```

### Restore

```bash
docker compose down
docker compose exec -T postgres psql -U postgres langfuse < /backups/langfuse_20260513.sql
docker compose up -d
```

---

## SSL / HTTPS (Recommended for Production)

Use nginx as reverse proxy:

```nginx
server {
    listen 443 ssl;
    server_name langfuse.internal.company.com;

    ssl_certificate     /etc/ssl/certs/langfuse.crt;
    ssl_certificate_key /etc/ssl/private/langfuse.key;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then update `LANGFUSE_HOST` in client `.env` to `https://langfuse.internal.company.com`.

---

## Scaling Considerations

| Scale | Recommendation |
|---|---|
| < 10 devs, < 1k traces/day | Single t3.medium, current setup |
| 10-50 devs, < 10k traces/day | t3.large, increase EBS to 100GB |
| 50+ devs, > 10k traces/day | Managed Postgres (RDS), separate ClickHouse, horizontal workers |

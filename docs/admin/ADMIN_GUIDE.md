# 🛠️ Admin Guide — Wrapper Development & Langfuse Management

> This section is for the **platform team** — people who maintain the
> `company-ai` SDK, manage the Langfuse instance, and handle infra.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Wrapper Development](#2-wrapper-development)
3. [Langfuse Server Management](#3-langfuse-server-management)
4. [Model Pricing Configuration](#4-model-pricing-configuration)
5. [User Onboarding Checklist](#5-user-onboarding-checklist)
6. [Monitoring & Maintenance](#6-monitoring--maintenance)
7. [Upgrading](#7-upgrading)
8. [Security Considerations](#8-security-considerations)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Developer's Application                            │
│                                                     │
│   from company_ai import AI                         │
│   client = AI(api_key=..., model=...)               │
│   client.chat(messages=[...], user_id=..., ...)     │
│                                                     │
└───────────────┬─────────────────────┬───────────────┘
                │                     │
                ▼                     ▼
┌───────────────────────┐  ┌─────────────────────────┐
│  Siemens LLM API      │  │  Langfuse (self-hosted)  │
│  (OpenAI-compatible)  │  │  EC2 / Docker Compose    │
│                       │  │                          │
│  - Inference          │  │  - Traces, spans         │
│  - Token counting     │  │  - Usage analytics       │
│                       │  │  - Cost tracking         │
└───────────────────────┘  │  - User/session grouping │
                           └─────────────────────────┘
```

**SDK flow:**
1. Developer calls `client.chat(...)`
2. `langfuse.openai.OpenAI` wrapper intercepts the call
3. `propagate_attributes()` sets trace-level user_id/session_id/tags
4. Request goes to Siemens LLM API
5. Response + metadata sent to Langfuse asynchronously
6. Developer gets the normal OpenAI response object

---

## 2. Wrapper Development

### File Structure

```
company_ai/
├── __init__.py       # Public exports (AI class)
├── client.py         # Main AI class — chat(), chat_stream()
├── config.py         # Environment variable loading
├── telemetry.py      # Langfuse client initialisation
└── exceptions.py     # Custom exceptions (future use)
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| `langfuse.openai.OpenAI` | Drop-in replacement — auto-captures all OpenAI calls |
| `propagate_attributes()` | Sets user_id/session_id/tags as first-class trace fields |
| `tenacity` retry | 3 attempts with exponential backoff for transient failures |
| `atexit.register(flush)` | No lost traces when process exits |
| Metadata dict | Team/app/env always attached for filtering |

### Making Changes

```bash
# Clone & install in dev mode
git clone https://github.com/Raiyan777/llm-observability-poc.git
cd project
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows
pip install -e ".[dev]"

# Run the POC test
python poc_test.py

# Lint
ruff check company_ai/
```

### Adding New Features

- **New method** (e.g. embeddings): Add to `client.py`, wrap with `propagate_attributes()`
- **New config var**: Add to `config.py` + `.env.example`
- **Bump version**: Update `version` in `pyproject.toml`

### Publishing Updates

```bash
# Tag a release
git tag v0.2.0
git push origin v0.2.0

# Users update via:
pip install --upgrade git+https://github.com/Raiyan777/llm-observability-poc.git
```

---

## 3. Langfuse Server Management

### Infrastructure

- **Hosting:** EC2 instance (t3.medium or larger)
- **IP:** `3.110.33.1`
- **Port:** `3000`
- **Stack:** Docker Compose with 6 containers

### Containers

| Container | Purpose | Port |
|---|---|---|
| `langfuse-web` | Web UI + API | 3000 |
| `langfuse-worker` | Async trace processing | — |
| `postgres` | Metadata storage | 5432 |
| `clickhouse` | Trace/analytics storage | — |
| `redis` | Queue / cache | 6379 |
| `minio` | Object storage (media) | 9000 |

### Common Operations

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@3.110.33.1

# Check status
cd /opt/langfuse
docker compose ps

# View logs
docker compose logs -f langfuse-web
docker compose logs -f langfuse-worker

# Restart
docker compose restart

# Full rebuild (after config changes)
docker compose down
docker compose up -d

# Backup Postgres
docker compose exec postgres pg_dump -U postgres langfuse > backup_$(date +%Y%m%d).sql
```

### Config Files on Server

```
/opt/langfuse/
├── docker-compose.yml    # Service definitions
├── .env                  # Server-side secrets (DB passwords, encryption keys)
```

---

## 4. Model Pricing Configuration

For the **Cost dashboard** to show values:

1. Go to **Langfuse → Settings → Models**
2. Click **+ Add Model**
3. Fill in:
   - **Model name:** The name returned by the API response (e.g. `qwen-3.6-27b`)
     > ⚠️ Use the **response** model name, not what you send in the request
   - **Input price per token:** e.g. `0.000001`
   - **Output price per token:** e.g. `0.000002`
4. Save

### Finding the Correct Model Name

The model name Langfuse uses comes from the API **response**, not your request.
Check any trace → generation → look at the `model` field. That's what to configure.

---

## 5. User Onboarding Checklist

When a new developer/team joins:

- [ ] Share `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
- [ ] Share `LLM_BASE_URL`
- [ ] Developer gets their own `LLM_API_KEY` from Siemens LLM portal
- [ ] Developer sets `TEAM_NAME` and `APPLICATION_NAME` for their project
- [ ] Point them to `docs/users/GETTING_STARTED.md`
- [ ] Add them to Langfuse UI (Settings → Members) if they need dashboard access
- [ ] Verify with: `client.auth_check()` returns `True`

---

## 6. Monitoring & Maintenance

### Health Checks

```bash
# Langfuse API health
curl http://3.110.33.1:3000/api/public/health

# Auth test from Python
from company_ai import AI
client = AI(api_key="any", model="any")
client.auth_check()  # True = server reachable
```

### Disk Space

ClickHouse + Postgres grow over time. Monitor with:

```bash
docker system df
df -h /var/lib/docker
```

### Log Rotation

Docker logs can grow large. Add to `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {"max-size": "50m", "max-file": "3"}
}
```

---

## 7. Upgrading

### Langfuse Server

```bash
cd /opt/langfuse
docker compose pull
docker compose down
docker compose up -d
```

Check [Langfuse releases](https://github.com/langfuse/langfuse/releases) for breaking changes.

### Python SDK (`langfuse` package)

```bash
pip install --upgrade langfuse
```

> ⚠️ Test with `poc_test.py` after upgrading — API surface can change between major versions.

### Wrapper (`company-ai`)

Update `version` in `pyproject.toml`, tag, push. Users run:

```bash
pip install --upgrade git+https://github.com/Raiyan777/llm-observability-poc.git
```

---

## 8. Security Considerations

| Concern | Mitigation |
|---|---|
| Secrets in `.env` | `.gitignore` — never committed |
| Prompts contain PII | Self-hosted Langfuse — data stays on your infra |
| Network exposure | Langfuse on private VPC, access via VPN or security group |
| API keys per developer | Revocable, auditable — each dev has their own `LLM_API_KEY` |
| Langfuse API keys | Rotate periodically in Settings → API Keys |
| DB backups | Schedule daily `pg_dump` to S3 or similar |

### Recommended Security Hardening

- Put Langfuse behind an **internal load balancer** (no public IP)
- Enable **HTTPS** with a certificate (reverse proxy via nginx/ALB)
- Restrict EC2 security group to company VPN CIDR
- Use **IAM roles** for EC2 instead of static AWS credentials

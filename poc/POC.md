# 🧪 POC Guide — LLM Observability with Langfuse

> **Goal:** Deploy a self-hosted Langfuse instance + internal Python SDK that
> gives any developer automatic tracing of all LLM calls (prompt, response,
> tokens, cost, latency, errors) with zero manual instrumentation.

---

## Prerequisites

| Item | Details |
|---|---|
| AWS EC2 | t3.medium (or larger), 30GB EBS, ports 3000 + 22 open |
| Docker + Docker Compose | v2.x on EC2 |
| Python 3.10+ | On your local machine |
| Git | Access to this repo |
| Siemens LLM API key | Per-developer, from internal portal |

---

## Phase 1 — Deploy Langfuse Server (EC2)

### 1.1 SSH into EC2

```bash
ssh -i your-key.pem ec2-user@<EC2_IP>
```

### 1.2 Install Docker (if not already)

```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Re-login for group change
exit
ssh -i your-key.pem ec2-user@<EC2_IP>
```

### 1.3 Set up Langfuse

```bash
sudo mkdir -p /opt/langfuse && cd /opt/langfuse
```

Copy the files from this repo's `infra/` folder:
- `infra/docker-compose.yml` → `/opt/langfuse/docker-compose.yml`
- `infra/.env.example` → `/opt/langfuse/.env` (then fill in real values)

```bash
# Generate secrets
openssl rand -hex 32    # Use for NEXTAUTH_SECRET
openssl rand -hex 32    # Use for ENCRYPTION_KEY
openssl rand -hex 16    # Use for SALT
openssl rand -hex 16    # Use for passwords
```

### 1.4 Start Langfuse

```bash
cd /opt/langfuse
docker compose up -d
```

Wait ~30 seconds, then verify:

```bash
curl http://localhost:3000/api/public/health
# Should return: {"status":"OK"}
```

### 1.5 Access Langfuse UI

Open in browser: `http://<EC2_IP>:3000`

Login with the credentials you set in `.env`:
- Email: `LANGFUSE_INIT_USER_EMAIL`
- Password: `LANGFUSE_INIT_USER_PASSWORD`

### 1.6 Get API Keys

Go to **Settings → API Keys** and note:
- `Public Key` → `pk-lf-...`
- `Secret Key` → `sk-lf-...`

These go into the client-side `.env` (Phase 2).

---

## Phase 2 — Set Up the SDK (Local Machine)

### 2.1 Clone this repo

```bash
git clone https://github.com/Raiyan777/llm-observability-poc.git
cd project
```

### 2.2 Create Python environment

```bash
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Linux/Mac:
source .venv/bin/activate

pip install -e .
```

### 2.3 Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```dotenv
# Langfuse server (from Phase 1.6)
LANGFUSE_HOST=http://<EC2_IP>:3000
LANGFUSE_PUBLIC_KEY=pk-lf-your-key
LANGFUSE_SECRET_KEY=sk-lf-your-key

# LLM endpoint
LLM_BASE_URL=https://api.siemens.com/llm/v1

# Your context
TEAM_NAME=your-team
APPLICATION_NAME=your-app
ENVIRONMENT=dev

# Your credentials
LLM_API_KEY=your-personal-key
LLM_MODEL_NAME=qwen3-30b-a3b-instruct-2507
```

### 2.4 Run the POC test

```bash
python poc/poc_test.py
```

**Expected output:**

```
Checking Langfuse connection...
  ✅ Langfuse OK

─── Test 1: Traced pipeline (nested spans) ───
  ✅ Answer: AI observability is the practice of...

─── Test 2: Multi-turn session ───
  Turn 1 ✅: LLM observability is...
  Turn 2 ✅: It is important because...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ All traces sent — check your Langfuse dashboard
```

### 2.5 Verify in Langfuse Dashboard

Open `http://<EC2_IP>:3000` and check:

| Dashboard | What you should see |
|---|---|
| **Traces** | `answer-pipeline` with nested spans + `multi-turn-chat` traces |
| **Sessions** | `poc-session-001` with 2 linked turns |
| **Users** | `poc-tester` with aggregated usage |
| **Dashboard** | Total tokens, latency P50/P95 |
| **Cost** | Token usage per model (configure pricing in Settings → Models) |

---

## Phase 3 — Configure Model Pricing (Optional but Recommended)

1. Go to **Langfuse → Settings → Models**
2. Click **+ Add Model**
3. Model name: use the name from the **API response** (check any trace → generation → model field, e.g. `qwen-3.6-27b`)
4. Set input/output price per token
5. Save → Cost dashboard populates

---

## Phase 4 — Roll Out to Developers

### What developers need:

1. `pip install git+https://github.com/Raiyan777/llm-observability-poc.git`
2. A `.env` file with shared Langfuse keys + their personal LLM key
3. Point them to `docs/users/GETTING_STARTED.md`

### Minimal developer code:

```python
from company_ai import AI

client = AI(api_key="your-key", model="your-model")
response = client.chat(
    messages=[{"role": "user", "content": "Hello"}],
    user_id="developer-name",
    tags=["their-team"],
)
print(response.choices[0].message.content)
```

Everything else is automatic.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `auth_check()` fails | Check `LANGFUSE_HOST`, `PUBLIC_KEY`, `SECRET_KEY` in `.env` |
| Traces not appearing | Call `client.flush()` or wait a few seconds |
| Cost shows $0 | Add model pricing in Settings → Models |
| `Connection refused` | EC2 security group must allow port 3000 inbound |
| `Completions.create() got unexpected kwarg` | Update the SDK: `pip install -e .` (bug was fixed) |
| Docker containers crashing | Check logs: `docker compose logs langfuse-web` |
| Disk full on EC2 | ClickHouse data grows — increase EBS or add retention policy |

---

## Files Reference

```
.
├── company_ai/              # SDK package (what developers import)
│   ├── __init__.py
│   ├── client.py            # AI class — the wrapper
│   ├── config.py            # Env var loading
│   ├── telemetry.py         # Langfuse client init
│   └── exceptions.py
├── infra/                   # Server deployment
│   ├── docker-compose.yml   # Langfuse v3 stack (6 containers)
│   └── .env.example         # Server-side secrets template
├── docs/
│   ├── users/               # For developers using the SDK
│   │   ├── GETTING_STARTED.md
│   │   ├── USAGE_EXAMPLES.md
│   │   └── API_REFERENCE.md
│   └── admin/               # For platform team
│       ├── ADMIN_GUIDE.md
│       └── DEPLOYMENT.md
├── examples/
│   └── poc_test.py          # End-to-end validation script
├── .env.example             # Client-side env template
├── pyproject.toml           # Package config
├── .gitignore
└── README.md                # Project overview + links
```

# ============================================================
#  LANGFUSE POC — STEP-BY-STEP GUIDE (Langfuse v3)
# ============================================================
#
#  This guide has 2 phases:
#    PHASE 1: Deploy Langfuse v3 server on EC2
#    PHASE 2: Run the SDK from your local machine and verify traces
#
#  Services: langfuse-web, langfuse-worker, postgres, clickhouse,
#            redis, minio  (6 containers total)
#
#  Reference: https://langfuse.com/self-hosting/deployment/docker-compose
#
# ============================================================


# ████████████████████████████████████████████████████████████
#  PHASE 1: DEPLOY LANGFUSE ON EC2
# ████████████████████████████████████████████████████████████


# ────────────────────────────────────────────────────────────
#  STEP 1.1 — CREATE AN EC2 INSTANCE
# ────────────────────────────────────────────────────────────
#
#  Go to AWS Console > EC2 > Launch Instance
#
#    Name:            langfuse-poc
#    AMI:             Ubuntu Server 22.04 LTS
#    Instance type:   t3.large  (2 vCPU, 8 GB RAM — recommended)
#    Storage:         30 GB gp3
#    Key pair:        Select or create one (you'll need the .pem file)
#
#  Security Group — Inbound rules:
#    ┌──────────┬──────────┬─────────────────────┐
#    │ Port     │ Protocol │ Source               │
#    ├──────────┼──────────┼─────────────────────┤
#    │ 22       │ TCP      │ Your IP              │
#    │ 3000     │ TCP      │ Your IP / Office IP  │
#    └──────────┴──────────┴─────────────────────┘
#
#  Click "Launch Instance" and wait for it to start.
#  Note down the PUBLIC IP address.


# ────────────────────────────────────────────────────────────
#  STEP 1.2 — SSH INTO THE EC2 INSTANCE
# ────────────────────────────────────────────────────────────

ssh ubuntu@YOUR_EC2_PUBLIC_IP


# ────────────────────────────────────────────────────────────
#  STEP 1.3 — UPDATE SYSTEM & INSTALL DOCKER (run on EC2)
# ────────────────────────────────────────────────────────────

sudo apt-get update -y
sudo apt-get upgrade -y

sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings

# Add Docker GPG key
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

# Install Docker + Compose
sudo apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# Enable docker without sudo
sudo usermod -aG docker ubuntu
newgrp docker

# Verify
docker run hello-world
docker compose version


# ────────────────────────────────────────────────────────────
#  STEP 1.4 — GENERATE SECRETS (run on EC2)
# ────────────────────────────────────────────────────────────
#
#  Run each command, SAVE the output. You will paste these into
#  the .env file in step 1.6.

# NEXTAUTH_SECRET (64 hex chars)
openssl rand -hex 32

# ENCRYPTION_KEY (64 hex chars — REQUIRED for Langfuse v3)
openssl rand -hex 32

# SALT (64 hex chars)
openssl rand -hex 32

# POSTGRES_PASSWORD
openssl rand -hex 16

# CLICKHOUSE_PASSWORD
openssl rand -hex 16

# REDIS_AUTH
openssl rand -hex 16

# MINIO_ROOT_PASSWORD
openssl rand -hex 16


# ────────────────────────────────────────────────────────────
#  STEP 1.5 — CREATE WORKING DIRECTORY (run on EC2)
# ────────────────────────────────────────────────────────────

mkdir -p ~/langfuse
cd ~/langfuse


# ────────────────────────────────────────────────────────────
#  STEP 1.6 — CREATE .env FILE (run on EC2)
# ────────────────────────────────────────────────────────────
#
#  OPTION A — Auto-generate everything (recommended):
#  Replace YOUR_EC2_PUBLIC_IP with your actual IP, then run:

PUBLIC_IP="YOUR_EC2_PUBLIC_IP"

cat > .env <<EOF
# ── Langfuse v3 server .env ──
# Generated on $(date -u +%Y-%m-%dT%H:%M:%SZ)

NEXTAUTH_URL=http://${PUBLIC_IP}:3000
NEXTAUTH_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
SALT=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
CLICKHOUSE_PASSWORD=$(openssl rand -hex 16)
REDIS_AUTH=$(openssl rand -hex 16)
MINIO_ROOT_PASSWORD=$(openssl rand -hex 16)
EOF

#
#  OPTION B — Manual: paste the secrets from step 1.4:
#
cat > .env <<'EOF'
NEXTAUTH_URL=http://3.110.33.1:3000
NEXTAUTH_SECRET=dc05ea69e6f34dbe6c79852e9e8617007b2e7cc5221eec3172a6c5316d8f89e2
ENCRYPTION_KEY=ad4d2c245336b777e84653ce017389a5bebd352b1d9b9bf3029a8241d31e39ad
SALT=9dcdc098f66ee7736a97dd67e140863cf95281f90beae5990f9c0885962840ca
POSTGRES_PASSWORD=aaf74d4abdb4c04b4a1b6b6b767391d8
CLICKHOUSE_PASSWORD=a6949c4d4bd02193316a4a51e8d323a2
REDIS_AUTH=a0018a3b3d7beaa0007319be928cd0ae
MINIO_ROOT_PASSWORD=e5e3e3c71dc1082879341a8cc77d925f
EOF


# Verify (secrets should be filled, not placeholders):
cat .env


# ────────────────────────────────────────────────────────────
#  STEP 1.7 — GET docker-compose.yml (run on EC2)
# ────────────────────────────────────────────────────────────
#
#  Pick ONE of these options:
#
#  Option A — Clone the official Langfuse repo (easiest):

git clone https://github.com/langfuse/langfuse.git /tmp/langfuse-repo
cp /tmp/langfuse-repo/docker-compose.yml ~/langfuse/

#  Option B — Copy from your local machine:
#    scp docker-compose.yml ubuntu@YOUR_EC2_PUBLIC_IP:~/langfuse/
#
#  Option C — Download directly from GitHub:
#    curl -L -o ~/langfuse/docker-compose.yml \
#      https://raw.githubusercontent.com/langfuse/langfuse/main/docker-compose.yml
#
#  NOTE: The official compose file reads ALL secrets from .env
#  via ${VARIABLE} syntax. No hardcoded passwords.
#
#  ⚠️  If using the official file, update the default secret
#  placeholders (mysalt, mysecret, etc.) in .env — which you
#  already did in step 1.6.


# ────────────────────────────────────────────────────────────
#  STEP 1.8 — START LANGFUSE (run on EC2)
# ────────────────────────────────────────────────────────────

cd ~/langfuse
docker compose up -d

# Wait 60-90 seconds for all containers to start, then check:
docker compose ps

# You should see 6 containers running:
#   langfuse-web-1       (port 3000)        ← the UI
#   langfuse-worker-1                       ← background processor
#   postgres-1           (healthy)          ← main database
#   clickhouse-1         (healthy)          ← analytics database
#   redis-1              (healthy)          ← cache/queue
#   minio-1              (port 9090)        ← blob storage

# If any container is restarting, check logs:
docker compose logs langfuse-web
docker compose logs langfuse-worker


# ────────────────────────────────────────────────────────────
#  STEP 1.9 — OPEN LANGFUSE DASHBOARD
# ────────────────────────────────────────────────────────────
#
#  Open in browser (incognito recommended):
#
#    http://YOUR_EC2_PUBLIC_IP:3000
#
#  1. Click "Sign Up"
#  2. Create your account (first user = admin)
#  3. Create an Organization (e.g. "My Company")
#  4. Create a Project (e.g. "AI Observability POC")


# ────────────────────────────────────────────────────────────
#  STEP 1.10 — CREATE API KEYS IN LANGFUSE
# ────────────────────────────────────────────────────────────
#
#  In the Langfuse dashboard:
#
#  1. Go to Settings (gear icon) > API Keys
#  2. Click "Create API Key"
#  3. SAVE THESE VALUES — you need them in Phase 2:
#
#     Public Key:  pk-
#     Secret Key:  sk-
#
#  ✅ PHASE 1 COMPLETE — Langfuse is running!


# ████████████████████████████████████████████████████████████
#  PHASE 2: SET UP SDK ON YOUR LOCAL MACHINE
# ████████████████████████████████████████████████████████████


# ────────────────────────────────────────────────────────────
#  STEP 2.1 — CLONE THE REPO (run on your local machine)
# ────────────────────────────────────────────────────────────
#
#  If you pushed to git:

git clone https://your-git-server.com/your-org/company-ai.git
cd company-ai

#  Or if working from the existing folder:

cd C:\Users\z004zbdd\Documents\langfuse


# ────────────────────────────────────────────────────────────
#  STEP 2.2 — CREATE A PYTHON VIRTUAL ENVIRONMENT
# ────────────────────────────────────────────────────────────

python -m venv .venv

# Activate it:
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Linux/Mac:
# source .venv/bin/activate


# ────────────────────────────────────────────────────────────
#  STEP 2.3 — INSTALL THE SDK
# ────────────────────────────────────────────────────────────

pip install -e .

# This installs company_ai + all dependencies (openai, langfuse, tenacity, etc.)
# Verify:
pip list | findstr "langfuse openai tenacity"


# ────────────────────────────────────────────────────────────
#  STEP 2.4 — CREATE YOUR .env FILE
# ────────────────────────────────────────────────────────────
#
#  Copy the example and edit it:
#
#  Windows PowerShell:

Copy-Item .env.example .env

#  Linux/Mac:
#  cp .env.example .env
#
#  Now open .env in your editor and fill in REAL values:
#
#  ┌──────────────────────────────────────────────────────────┐
#  │  LANGFUSE_HOST=http://YOUR_EC2_PUBLIC_IP:3000            │
#  │  LANGFUSE_PUBLIC_KEY=pk-lf-xxxx    ← from Step 1.10     │
#  │  LANGFUSE_SECRET_KEY=sk-lf-xxxx    ← from Step 1.10     │
#  │  LLM_BASE_URL=https://your-internal-llm-api.com/v1      │
#  │  TEAM_NAME=platform-team                                 │
#  │  APPLICATION_NAME=poc-app                                │
#  │  ENVIRONMENT=dev                                         │
#  │  LLM_API_KEY=your-personal-llm-key                      │
#  │  LLM_MODEL_NAME=your-model-name                         │
#  └──────────────────────────────────────────────────────────┘


# ────────────────────────────────────────────────────────────
#  STEP 2.5 — RUN THE POC TEST
# ────────────────────────────────────────────────────────────

python poc_test.py

# Expected output:
#
#   Checking Langfuse connection...
#     ✅ Langfuse OK
#
#   Sending traced LLM call...
#     ✅ Response: AI observability is the practice of...
#
#     ✅ Trace sent — check your Langfuse dashboard!


# ────────────────────────────────────────────────────────────
#  STEP 2.6 — VERIFY IN LANGFUSE DASHBOARD
# ────────────────────────────────────────────────────────────
#
#  1. Open http://YOUR_EC2_PUBLIC_IP:3000
#  2. Go to your project
#  3. Click "Traces" in the left sidebar
#  4. You should see a trace with:
#     ┌─────────────────────────────────────────┐
#     │  ✔ Prompt messages                      │
#     │  ✔ LLM response                         │
#     │  ✔ Model name                            │
#     │  ✔ Token usage (input/output/total)      │
#     │  ✔ Latency                               │
#     │  ✔ user_id = "poc-tester"                │
#     │  ✔ tags = ["poc", "validation"]          │
#     │  ✔ metadata = team, application, env     │
#     └─────────────────────────────────────────┘
#
#  ✅ POC COMPLETE!


# ████████████████████████████████████████████████████████████
#  TROUBLESHOOTING
# ████████████████████████████████████████████████████████████
#
#  PROBLEM: Can't reach http://EC2_IP:3000
#  FIX:     Check EC2 Security Group has port 3000 open to your IP
#           Run: docker compose ps   (all 6 containers should be running/healthy)
#           Run: docker compose logs langfuse-web   (check for errors)
#
#  PROBLEM: langfuse-web or langfuse-worker keeps restarting
#  FIX:     Run: docker compose logs langfuse-web
#           Common causes:
#             - Missing ENCRYPTION_KEY in .env (REQUIRED for v3)
#             - Missing or wrong NEXTAUTH_SECRET / SALT
#             - postgres/clickhouse not healthy yet — wait 60s & retry
#             - NEXTAUTH_URL not set to http://YOUR_EC2_IP:3000
#
#  PROBLEM: poc_test.py says "Langfuse FAILED"
#  FIX:     Check LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY in .env
#           Make sure the URL is http:// not https:// (no SSL on POC)
#           Make sure there's no trailing slash on the URL
#
#  PROBLEM: poc_test.py says "LLM call FAILED"
#  FIX:     Check LLM_BASE_URL points to your internal LLM API
#           Check LLM_API_KEY is valid
#           Check LLM_MODEL_NAME is a valid model on your internal API
#
#  PROBLEM: Trace appears in Langfuse but token counts are missing
#  FIX:     Your internal LLM API may not return usage data
#           This is an API-side issue, not an SDK issue
#
#  PROBLEM: docker compose up fails with port conflict
#  FIX:     Another service is using port 3000, 9000, or 9001
#           Run: sudo lsof -i :3000   to find what's using it
#           Change the host port in docker-compose.yml
#
#  USEFUL COMMANDS:
#    docker compose ps              # check all container status
#    docker compose logs -f         # tail all logs
#    docker compose down            # stop everything
#    docker compose up -d           # start everything
#    docker compose down -v         # stop + DELETE all data (nuclear reset)

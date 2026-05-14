# company-ai

> Internal AI SDK with automatic LLM observability via Langfuse.

**One wrapper. Zero instrumentation. Full tracing.**

Every LLM call made through this SDK is automatically traced — prompt, response,
tokens, latency, cost, errors, user, and session — with no extra code required.

---

## Quick Start

> **New here?** Follow the **[POC Guide](poc/POC.md)** — it covers everything
> from server deployment to your first traced LLM call.

```bash
pip install git+https://github.com/Raiyan777/llm-observability-poc.git
```

```python
from company_ai import AI

client = AI(api_key="your-key", model="your-model")
response = client.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    user_id="your-name",
)
print(response.choices[0].message.content)
```

---

## 📚 Documentation

### For Developers / Users (using the wrapper)

| Doc | Description |
|---|---|
| [Getting Started](docs/users/GETTING_STARTED.md) | Installation, env setup, first call |
| [Usage Examples](docs/users/USAGE_EXAMPLES.md) | Sessions, tags, streaming, nested pipelines |
| [API Reference](docs/users/API_REFERENCE.md) | All parameters, return types, auto-captured signals |

### For Admins / Platform Team (maintaining the wrapper & infra)

| Doc | Description |
|---|---|
| [Admin Guide](docs/admin/ADMIN_GUIDE.md) | Architecture, wrapper development, Langfuse management, onboarding |
| [Deployment](docs/admin/DEPLOYMENT.md) | EC2 setup, Docker Compose, backups, SSL, scaling |

---

## Project Structure

```
.
├── poc/                     # 🧪 POC — START HERE
│   ├── POC.md               # Full end-to-end guide
│   └── poc_test.py          # Validation script
├── company_ai/              # SDK package (pip-installable)
│   ├── __init__.py          # Public exports
│   ├── client.py            # AI class — chat(), chat_stream()
│   ├── config.py            # Org-level defaults (Langfuse host, keys baked in)
│   ├── guardrails.py        # Prompt scanner (PII, jailbreak, blocklist)
│   ├── telemetry.py         # Langfuse client init
│   └── exceptions.py        # Custom exception classes
├── infra/                   # Server deployment
│   ├── docker-compose.yml   # Langfuse v3 stack (6 containers)
│   └── .env.example         # Server-side secrets template
├── docs/
│   ├── users/               # 👩‍💻 For developers using the SDK
│   │   ├── GETTING_STARTED.md
│   │   ├── USAGE_EXAMPLES.md
│   │   └── API_REFERENCE.md
│   └── admin/               # 🔧 For platform team
│       ├── ADMIN_GUIDE.md
│       └── DEPLOYMENT.md
├── .env.example             # Client-side env template (optional overrides)
├── pyproject.toml           # Package build config
├── .gitignore
└── README.md                # ← You are here
```

---

## What Gets Traced Automatically

| Signal | Dashboard |
|---|---|
| Prompt & response | Traces |
| Token usage | Usage |
| Latency | Traces |
| Cost | Cost (requires model pricing config) |
| Errors + retries | Traces (error filter) |
| User ID | Users |
| Session ID | Sessions |
| Tags | Tag filter |
| Team / App / Env | Metadata |
| Guardrail violations | Tag: `guardrail-flagged` + metadata details |

---

## Need Help?

- **Using the wrapper?** → Start with [Getting Started](docs/users/GETTING_STARTED.md)
- **Managing infra?** → See [Admin Guide](docs/admin/ADMIN_GUIDE.md)
- **Platform team Slack/Teams:** `#llm-observability`

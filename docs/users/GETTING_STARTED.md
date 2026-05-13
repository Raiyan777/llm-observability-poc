# 🚀 Getting Started — company-ai SDK

> **One wrapper. Zero instrumentation. Full observability.**
>
> `company-ai` is an internal Python SDK that gives you an OpenAI-compatible
> LLM client with **automatic tracing**. Every call is recorded — prompt,
> response, tokens, latency, cost, and errors — without any extra code.
>
> **You don't need to configure Langfuse.** The connection is baked into the package.

---

## 1. Installation

```bash
# From Git (recommended)
pip install git+https://github.com/Raiyan777/project.git

# Or clone locally
git clone https://github.com/Raiyan777/project.git
cd project
pip install -e .
```

---

## 2. Usage — That's It

You only need **two things you already have**: your LLM API key and model name.

```python
from company_ai import AI

client = AI(api_key="YOUR_LLM_API_KEY", model="YOUR_MODEL_NAME")

response = client.chat(
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

✅ **Done.** The call is already traced in Langfuse — no setup, no config files, no env vars needed.

---

## 3. Optional: Add Context for Better Dashboard Filtering

These are **optional** — the tracing works without them, but they make
the Langfuse dashboards more useful for your team:

```python
client = AI(
    api_key="YOUR_LLM_API_KEY",
    model="YOUR_MODEL_NAME",
    team="your-team-name",          # Shows up in trace metadata
    application="your-app-name",    # Shows up in trace metadata
)

response = client.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    user_id="jane.doe@siemens.com",   # → Users dashboard
    session_id="conv-abc-123",        # → Sessions dashboard (multi-turn)
    tags=["production", "v2"],        # → Tag filter in sidebar
)
```

### Or use environment variables (optional)

If you prefer env vars over constructor args, create a `.env`:

```dotenv
TEAM_NAME=your-team
APPLICATION_NAME=your-app
ENVIRONMENT=dev
```

> ⚠️ **You do NOT need** `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, or
> `LANGFUSE_SECRET_KEY`. Those are already configured inside the package.

---

## 4. What You Get (Automatically)

| Signal | Where to see it |
|---|---|
| Prompt & response | Langfuse → Traces → click any trace |
| Token usage | Usage dashboard |
| Latency | Traces list |
| Cost | Cost dashboard |
| Errors + retries | Traces (error filter) |

Dashboard URL: **`http://observability.siemens.com`** (or ask platform team for the current URL)

---

## Next Steps

- **[Usage Examples →](./USAGE_EXAMPLES.md)** — sessions, tags, streaming, pipelines
- **[API Reference →](./API_REFERENCE.md)** — all parameters explained

"""
Configuration — org-level defaults baked in, per-developer values at runtime.

Langfuse connection and LLM base URL are FIXED for the entire company.
Developers only provide: api_key, model (via constructor), and optionally
team/app/environment context.
"""

import os

from dotenv import load_dotenv

load_dotenv(override=False)  # .env can override defaults, but isn't required

# ══════════════════════════════════════════════════════════════════════
# ORG-LEVEL DEFAULTS (baked into the package — developers don't touch these)
# ══════════════════════════════════════════════════════════════════════

# Langfuse observability server (self-hosted, company-wide)
LANGFUSE_HOST: str = os.getenv(
    "LANGFUSE_HOST",
    "http://3.110.33.1:3000",  # TODO: Replace with https://observability.siemens.com once DNS is set up
)
LANGFUSE_PUBLIC_KEY: str = os.getenv(
    "LANGFUSE_PUBLIC_KEY",
    "pk-lf-9d457021-16dc-4528-a36a-a64a4a8b1997",
)
LANGFUSE_SECRET_KEY: str = os.getenv(
    "LANGFUSE_SECRET_KEY",
    "sk-lf-26d86424-fa08-4d09-bd48-e07ec4527f7c",
)

# Internal LLM endpoint (company-wide, same for everyone)
LLM_BASE_URL: str = os.getenv(
    "LLM_BASE_URL",
    "https://api.siemens.com/llm/v1",
)

# ══════════════════════════════════════════════════════════════════════
# PER-TEAM / PER-APP CONTEXT (optional — for filtering in dashboards)
# ══════════════════════════════════════════════════════════════════════

TEAM_NAME: str = os.getenv("TEAM_NAME", "unknown-team")
APPLICATION_NAME: str = os.getenv("APPLICATION_NAME", "unknown-app")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

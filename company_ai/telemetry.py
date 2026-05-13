"""
Telemetry — Langfuse client initialisation.
"""

from langfuse import Langfuse

from company_ai.config import (
    LANGFUSE_HOST,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
)

langfuse = Langfuse(
    host=LANGFUSE_HOST,
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
)

"""
AI client — auto-instrumented via langfuse.openai + propagate_attributes.

All LLM calls are automatically traced: prompt, response, tokens, latency,
model, cost, and errors — with zero manual instrumentation.

Trace-level attributes (user_id, session_id, tags) are set via the SDK's
``propagate_attributes`` context manager so they appear as **first-class
fields** in Langfuse dashboards (Users, Sessions, tag filters) — not just
buried inside metadata.
"""

import atexit

from langfuse.openai import OpenAI
from langfuse._client.propagation import propagate_attributes
from tenacity import retry, stop_after_attempt, wait_exponential

from company_ai.config import (
    LLM_BASE_URL,
    TEAM_NAME,
    APPLICATION_NAME,
    ENVIRONMENT,
)
from company_ai.guardrails import scan_prompt, ScanResult
from company_ai.telemetry import langfuse

# Ensure pending traces are flushed when the process exits.
atexit.register(langfuse.flush)


class AI:
    """
    Internal AI client with automatic observability.

    Usage:
        client = AI(api_key="your-key", model="your-model")
        response = client.chat([{"role": "user", "content": "Hello"}])
        print(response.choices[0].message.content)

    Every call populates:
        ✅ Traces      — prompt, response, latency, errors
        ✅ Usage       — prompt / completion tokens
        ✅ Cost        — token-based cost (configure model pricing in Langfuse)
        ✅ Users       — per-user analytics  (via user_id)
        ✅ Sessions    — multi-turn grouping  (via session_id)
        ✅ Tags        — filterable labels    (via tags)
        ✅ Metadata    — team, app, env + arbitrary key-values
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        team: str | None = None,
        application: str | None = None,
    ):
        self.model = model
        self.team = team or TEAM_NAME
        self.application = application or APPLICATION_NAME

        self._client = OpenAI(
            base_url=base_url or LLM_BASE_URL,
            api_key=api_key,
        )

    def _base_metadata(self, extra: dict | None = None) -> dict:
        """Build the metadata dict with team/app/env context."""
        meta: dict = {
            "team": self.team,
            "application": self.application,
            "environment": ENVIRONMENT,
        }
        if extra:
            meta.update(extra)
        return meta

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
    )
    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        user_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
        session_id: str | None = None,
        **kwargs,
    ):
        """
        Send a chat completion request.  Fully auto-traced to Langfuse.

        Args:
            messages:   OpenAI-format messages list.
            model:      Override the default model for this call.
            user_id:    Identify the end-user  → populates **Users** dashboard.
            tags:       Filterable tags         → sidebar tag filter.
            metadata:   Arbitrary key-value     → trace detail view.
            session_id: Group related calls     → populates **Sessions** dashboard.
            **kwargs:   Any OpenAI param (temperature, max_tokens, etc.).
        """
        merged_metadata = self._base_metadata(metadata)

        # ── Guardrail scan ──
        prompt_text = " ".join(
            m.get("content", "") for m in messages if m.get("role") == "user"
        )
        scan = scan_prompt(prompt_text)

        call_tags = list(tags or [])
        if scan.flagged:
            call_tags.append("guardrail-flagged")
            merged_metadata["guardrail_violations"] = scan.summary

        with propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            tags=call_tags,
            metadata=merged_metadata,
        ):
            response = self._client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                metadata=merged_metadata,
                **kwargs,
            )
        return response

    def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        user_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
        session_id: str | None = None,
        **kwargs,
    ):
        """Streaming variant — yields chunks, still fully traced."""
        merged_metadata = self._base_metadata(metadata)

        # ── Guardrail scan ──
        prompt_text = " ".join(
            m.get("content", "") for m in messages if m.get("role") == "user"
        )
        scan = scan_prompt(prompt_text)

        call_tags = list(tags or [])
        if scan.flagged:
            call_tags.append("guardrail-flagged")
            merged_metadata["guardrail_violations"] = scan.summary

        with propagate_attributes(
            user_id=user_id,
            session_id=session_id,
            tags=call_tags,
            metadata=merged_metadata,
        ):
            response = self._client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                stream=True,
                metadata=merged_metadata,
                **kwargs,
            )
            for chunk in response:
                yield chunk

    def flush(self):
        """Flush pending traces to Langfuse (call before process exit)."""
        langfuse.flush()

    def auth_check(self) -> bool:
        """Verify Langfuse connectivity."""
        return langfuse.auth_check()

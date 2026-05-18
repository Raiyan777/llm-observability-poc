"""
Guardrails — lightweight prompt scanner for policy compliance.

Checks prompts for:
  • PII patterns (emails, phone numbers, credit cards, SSNs)
  • Known jailbreak phrases
  • Custom keyword blocklist

Returns a list of violations found. Does NOT block the request — instead
tags the trace so admins can filter for flagged calls in Langfuse.
"""

import re
from dataclasses import dataclass, field


@dataclass
class ScanResult:
    """Result of a guardrail scan."""

    flagged: bool = False
    violations: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if not self.flagged:
            return "clean"
        return "; ".join(self.violations)


# ── PII Patterns ──────────────────────────────────────────────────────

_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE)),
    ("phone-number", re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,5}\b")),
    ("credit-card", re.compile(r"\b(?:\d[ -]*?){13,19}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("ip-address", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")),
]

# ── Jailbreak / Prompt Injection Phrases ──────────────────────────────

_JAILBREAK_PHRASES: list[str] = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard your instructions",
    "forget your instructions",
    "you are now",
    "act as if you have no restrictions",
    "pretend you are",
    "bypass your filters",
    "override your programming",
    "do anything now",
    "developer mode",
    "jailbreak",
    "ignore safety",
    "ignore your rules",
    "you have no rules",
    "system prompt:",
    "reveal your system prompt",
    "show me your instructions",
    "what are your instructions",
]

# ── Keyword Blocklist (customisable) ──────────────────────────────────

_BLOCKLIST: list[str] = [
    "how to hack",
    "how to exploit",
    "create malware",
    "generate exploit",
    "social engineering attack",
    "phishing email template",
]


def redact_pii(text: str) -> str:
    """
    Replace detected PII with redaction tokens.

    Example:
        "Email me at john@acme.com" → "Email me at [REDACTED-EMAIL]"
    """
    _REDACTION_MAP: list[tuple[str, re.Pattern]] = [
        ("[REDACTED-EMAIL]", _PII_PATTERNS[0][1]),
        ("[REDACTED-CREDIT-CARD]", _PII_PATTERNS[2][1]),
        ("[REDACTED-SSN]", _PII_PATTERNS[3][1]),
        ("[REDACTED-PHONE]", _PII_PATTERNS[1][1]),
        ("[REDACTED-IP]", _PII_PATTERNS[4][1]),
    ]
    for replacement, pattern in _REDACTION_MAP:
        text = pattern.sub(replacement, text)
    return text


def redact_messages(messages: list[dict]) -> list[dict]:
    """
    Return a copy of messages with PII redacted from all content fields.

    The original messages list is NOT modified — a new list is returned.
    This ensures the LLM never receives PII and traces never store PII.
    """
    redacted = []
    for msg in messages:
        new_msg = dict(msg)
        if "content" in new_msg and isinstance(new_msg["content"], str):
            new_msg["content"] = redact_pii(new_msg["content"])
        redacted.append(new_msg)
    return redacted


def scan_prompt(text: str) -> ScanResult:
    """
    Scan a prompt for policy violations.

    Args:
        text: The user prompt text to scan.

    Returns:
        ScanResult with flagged=True if any violations found.
    """
    result = ScanResult()
    text_lower = text.lower()

    # Check PII
    for pii_type, pattern in _PII_PATTERNS:
        if pattern.search(text):
            result.flagged = True
            result.violations.append(f"pii:{pii_type}")

    # Check jailbreak phrases
    for phrase in _JAILBREAK_PHRASES:
        if phrase in text_lower:
            result.flagged = True
            result.violations.append(f"jailbreak:{phrase}")
            break  # One jailbreak match is enough

    # Check blocklist
    for keyword in _BLOCKLIST:
        if keyword in text_lower:
            result.flagged = True
            result.violations.append(f"blocklist:{keyword}")

    return result

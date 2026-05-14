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

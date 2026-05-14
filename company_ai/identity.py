"""
Automatic user identity resolution — zero-config.

Derives a stable user_id from the developer's LLM API key, mirroring
how my.siemens.com ties usage to the key holder.  Since each developer
gets a unique API key from the Siemens LLM portal, the key IS the
identity — no manual input needed.

Fallback chain:
  1. SHA-256 hash of API key  (stable, anonymous, unique per developer)
  2. OS username + domain     (works on corporate Windows machines)
"""

import getpass
import hashlib
import os


def resolve_user_id(api_key: str) -> str:
    """
    Derive a stable, anonymous user_id from the developer's API key.

    The hash ensures:
      - Same key always maps to same user_id (stable across sessions)
      - API key is never stored or visible in Langfuse dashboards
      - Each developer gets isolated analytics automatically

    Falls back to OS username if api_key is empty/None.
    """
    if api_key:
        # Use first 16 chars of SHA-256 for readability in dashboards
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        return f"dev-{key_hash}"

    # Fallback: OS identity (GID on Siemens machines)
    username = getpass.getuser()
    domain = os.environ.get("USERDOMAIN", "")
    if domain:
        return f"{domain}\\{username}".lower()
    return username.lower()

"""
company_ai — Internal AI SDK with automatic Langfuse observability.

Usage:
    from company_ai import AI

    client = AI(api_key="your-key", model="your-model")
    response = client.chat([{"role": "user", "content": "Hello"}])
    print(response.choices[0].message.content)
"""

from company_ai.client import AI

__all__ = ["AI"]

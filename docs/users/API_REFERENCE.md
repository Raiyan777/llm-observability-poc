# 📋 API Reference

## `AI` Class

### Constructor

```python
AI(
    api_key: str,              # Required — your LLM API key
    model: str,                # Required — default model name
    base_url: str = None,      # Override LLM_BASE_URL env var
    team: str = None,          # Override TEAM_NAME env var
    application: str = None,   # Override APPLICATION_NAME env var
)
```

---

### `client.chat(...)`

Send a chat completion request. Automatically traced.

```python
client.chat(
    messages: list[dict],      # Required — OpenAI-format messages
    model: str = None,         # Override default model for this call
    user_id: str = None,       # End-user ID → Users dashboard
    session_id: str = None,    # Session ID → Sessions dashboard
    tags: list[str] = None,    # Filterable tags → sidebar filter
    metadata: dict = None,     # Arbitrary key-value (strings only)
    **kwargs,                  # Any OpenAI param (temperature, max_tokens, etc.)
)
```

**Returns:** `openai.types.chat.ChatCompletion`

**Retries:** Automatic — 3 attempts with exponential backoff (2s → 10s).

---

### `client.chat_stream(...)`

Same parameters as `chat()`. Returns a generator yielding chunks.

```python
for chunk in client.chat_stream(messages=[...]):
    print(chunk.choices[0].delta.content, end="")
```

**Returns:** `Generator[openai.types.chat.ChatCompletionChunk]`

---

### `client.flush()`

Force-send any pending traces to Langfuse. Called automatically on process exit.

---

### `client.auth_check()`

Verify Langfuse connectivity. Returns `True` if OK, raises on failure.

---

## What Gets Captured Automatically

| Signal | Dashboard |
|---|---|
| Prompt & response | Traces → detail view |
| Model name | Dashboard, model filter |
| Token usage (`prompt_tokens` + `completion_tokens`) | Usage dashboard |
| Latency (start → end) | Traces, latency column |
| Cost (tokens × pricing) | Cost dashboard |
| Errors + retry attempts | Traces (error filter) |
| Team / App / Environment | Metadata in trace detail |

---

## Supported `**kwargs` (OpenAI Parameters)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `temperature` | float | 1.0 | Randomness (0 = deterministic) |
| `max_tokens` | int | model limit | Max response tokens |
| `top_p` | float | 1.0 | Nucleus sampling |
| `frequency_penalty` | float | 0.0 | Penalise repeated tokens |
| `presence_penalty` | float | 0.0 | Penalise repeated topics |
| `stop` | list[str] | None | Stop sequences |
| `n` | int | 1 | Number of completions |
| `seed` | int | None | Reproducible outputs |

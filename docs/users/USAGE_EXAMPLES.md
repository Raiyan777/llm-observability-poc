# 📖 Usage Examples

## Basic Chat

```python
from company_ai import AI

client = AI(api_key="YOUR_KEY", model="YOUR_MODEL")

response = client.chat(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Summarise this document..."},
    ],
)
print(response.choices[0].message.content)
```

---

## User Tracking

```python
response = client.chat(
    messages=[{"role": "user", "content": "What is Kubernetes?"}],
    user_id="jane.doe@siemens.com",
)
```

- Appears in the **Users** dashboard
- Track per-user call volume, cost, latency

---

## Session Grouping (Multi-turn)

```python
session = "session-20260513-001"

# Turn 1
client.chat(messages=[{"role": "user", "content": "Hi"}], session_id=session)

# Turn 2
client.chat(messages=[{"role": "user", "content": "Follow up..."}], session_id=session)
```

- Groups all calls in the **Sessions** dashboard
- Great for chatbots & multi-step workflows

---

## Tags (Filterable Labels)

```python
client.chat(
    messages=[...],
    tags=["production", "search-team", "experiment-v2"],
)
```

- Filter traces by tag in the Langfuse sidebar

---

## Custom Metadata

```python
client.chat(
    messages=[...],
    metadata={
        "ticket": "JIRA-4521",
        "experiment": "prompt-v3",
        "source": "slack-bot",
    },
)
```

- Visible in trace detail view
- Values must be **strings**

---

## Streaming Responses

```python
for chunk in client.chat_stream(
    messages=[{"role": "user", "content": "Write a poem"}],
    user_id="dev-name",
    max_tokens=200,
):
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
print()
```

---

## Multi-step Pipelines (Nested Traces)

Use `@observe()` to create named, hierarchical traces:

```python
from langfuse import observe
from company_ai import AI

client = AI(api_key="YOUR_KEY", model="YOUR_MODEL")


@observe(name="classify-intent")
def classify(question: str) -> str:
    response = client.chat(
        messages=[
            {"role": "system", "content": "Classify: question/command/feedback"},
            {"role": "user", "content": question},
        ],
        max_tokens=10,
    )
    return response.choices[0].message.content.strip()


@observe(name="generate-answer")
def answer(question: str, intent: str) -> str:
    response = client.chat(
        messages=[
            {"role": "system", "content": f"Intent: {intent}. Answer concisely."},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


@observe(name="qa-pipeline")
def pipeline(question: str) -> str:
    intent = classify(question)
    return answer(question, intent)


result = pipeline("What is AI observability?")
```

This creates in Langfuse:
```
qa-pipeline
├── classify-intent
│   └── OpenAI-generation  (tokens, cost, latency)
└── generate-answer
    └── OpenAI-generation  (tokens, cost, latency)
```

---

## OpenAI Parameters

Any standard OpenAI parameter works as kwargs:

```python
response = client.chat(
    messages=[...],
    temperature=0.2,
    max_tokens=500,
    top_p=0.9,
    frequency_penalty=0.5,
    stop=["\n\n"],
)
```

---

## Combining Everything

```python
@observe(name="support-bot")
def handle_ticket(user_email: str, question: str, ticket_id: str):
    return client.chat(
        messages=[
            {"role": "system", "content": "You are a support agent."},
            {"role": "user", "content": question},
        ],
        user_id=user_email,
        session_id=f"ticket-{ticket_id}",
        tags=["support-bot", "production"],
        metadata={"ticket": ticket_id},
        temperature=0.3,
        max_tokens=300,
    )
```

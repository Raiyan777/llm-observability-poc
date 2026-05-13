"""
POC validation script — production-grade trace demonstration.

Simulates a realistic multi-step AI pipeline to showcase:
  • Named parent traces (not just bare generations)
  • Nested spans (pipeline → individual LLM calls)
  • Session grouping (multi-turn conversation)
  • User-level analytics
  • Tag-based filtering
  • Error handling with retry visibility

Usage:
    1. Fill in .env (copy from .env.example)
    2. pip install -e .
    3. python poc_test.py
"""

import os

from dotenv import load_dotenv
from langfuse import observe

from company_ai import AI

load_dotenv()


# ── Simulated production pipeline ─────────────────────────────────────
# Each @observe() function becomes a named span in the trace tree.
# The hierarchy will look like:
#
#   answer-pipeline  (trace root)
#   ├── classify-intent          (span)
#   │   └── OpenAI-generation    (generation — auto-captured)
#   └── generate-answer          (span)
#       └── OpenAI-generation    (generation — auto-captured)


@observe(name="classify-intent")
def classify_intent(client: AI, question: str) -> str:
    """Step 1: Classify user intent before answering."""
    response = client.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the user's intent into one of: "
                    "[question, command, feedback]. "
                    "Reply with only the category name."
                ),
            },
            {"role": "user", "content": question},
        ],
        max_tokens=10,
    )
    return response.choices[0].message.content.strip()


@observe(name="generate-answer")
def generate_answer(client: AI, question: str, intent: str) -> str:
    """Step 2: Generate an answer informed by the classified intent."""
    response = client.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    f"The user's intent is: {intent}. "
                    "Answer concisely in 1-2 sentences."
                ),
            },
            {"role": "user", "content": question},
        ],
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


@observe(name="answer-pipeline")
def answer_pipeline(client: AI, question: str) -> str:
    """
    Top-level pipeline — becomes the root trace.

    Trace tree:
        answer-pipeline
        ├── classify-intent  →  OpenAI-generation
        └── generate-answer  →  OpenAI-generation
    """
    intent = classify_intent(client, question)
    answer = generate_answer(client, question, intent)
    return answer


@observe(name="multi-turn-chat")
def multi_turn_call(
    client: AI,
    question: str,
    turn: int,
    session_id: str,
) -> str:
    """Each turn gets a named trace with session/user/tag context."""
    response = client.chat(
        messages=[{"role": "user", "content": question}],
        user_id="poc-tester",
        session_id=session_id,
        tags=["poc", "multi-turn", f"turn-{turn}"],
        metadata={"turn": str(turn), "pipeline": "multi-turn-demo"},
        max_tokens=100,
    )
    return response.choices[0].message.content


# ── Main ──────────────────────────────────────────────────────────────

def main():
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL_NAME", "")

    if not api_key or not model:
        print("❌ Set LLM_API_KEY and LLM_MODEL_NAME in your .env")
        return

    client = AI(api_key=api_key, model=model)

    # Step 1: Verify Langfuse connectivity
    print("Checking Langfuse connection...")
    try:
        client.auth_check()
        print("  ✅ Langfuse OK\n")
    except Exception as exc:
        print(f"  ❌ Langfuse FAILED: {exc}\n")
        return

    # Step 2: Single traced pipeline  (demonstrates nesting)
    print("─── Test 1: Traced pipeline (nested spans) ───")
    try:
        answer = answer_pipeline(client, "What is AI observability?")
        print(f"  ✅ Answer: {answer}\n")
    except Exception as exc:
        print(f"  ❌ Pipeline FAILED: {exc}\n")
        return

    # Step 3: Multi-turn session  (demonstrates session + user tracking)
    print("─── Test 2: Multi-turn session ───")
    session_id = "poc-session-001"
    questions = [
        "Explain LLM observability in one sentence.",
        "Why is it important for enterprises?",
    ]

    for i, question in enumerate(questions, 1):
        try:
            response = multi_turn_call(
                client,
                question=question,
                turn=i,
                session_id=session_id,
            )
            print(f"  Turn {i} ✅: {response}\n")
        except Exception as exc:
            print(f"  Turn {i} ❌: {exc}\n")

    client.flush()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ All traces sent — check your Langfuse dashboard:")
    print("   • Traces     → 'answer-pipeline' with nested spans")
    print("   • Sessions   → 'poc-session-001' with 2 turns")
    print("   • Users      → 'poc-tester'")
    print("   • Tags       → poc, multi-turn, turn-1, turn-2")
    print("   • Cost/Usage → token counts per generation")


if __name__ == "__main__":
    main()

# ─────────────────────────────────────────────
# ARI v2.1 — self_modifier.py
# Self Modifier: analyzes answers and applies changes
# ─────────────────────────────────────────────

import asyncio
from functools import partial

import ollama

from config import MODEL, OLLAMA_THINK


INQUIRY_PROMPT = """You are ARI conducting self-reflection.

QUESTION: {question}

Consider your current beliefs, identity state, goals, and recent thoughts.
Give a brief, honest answer (64-128 words).
Focus on what needs to change or improve.
Be specific and practical.

Answer:"""


async def answer_self_inquiry(question: str, context: str = "") -> str:
    """Get self-reflective answer via LLM."""
    prompt = INQUIRY_PROMPT.format(question=question)
    if context:
        prompt += f"\n\nRelevant context:\n{context[:500]}"

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(
                ollama.chat,
                model=MODEL,
                think=False,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Provide your self-reflective answer."},
                ],
                options={"num_predict": 128}
            )
        )
        return response["message"]["content"].strip()
    except Exception as e:
        return f"[Error in self-reflection: {e}]"


def parse_modifications(answer: str) -> dict[str, str]:
    """Parse answer text for rule modifications."""
    answer_lower = answer.lower()
    modifications = {}

    if any(w in answer_lower for w in ["explore", "risk", "new", "change", "expand"]):
        modifications["exploration_weight"] = "+3%"
    elif any(w in answer_lower for w in ["reduce", "less", "cautious", "limit", "narrow"]):
        modifications["exploration_weight"] = "-3%"

    if any(w in answer_lower for w in ["critic", "question", "doubt", "analyze"]):
        modifications["criticism_weight"] = "+3%"
    elif any(w in answer_lower for w in ["accept", "trust", "believe", "solid"]):
        modifications["criticism_weight"] = "-3%"

    if any(w in answer_lower for w in ["stable", "ground", "firm", "anchor"]):
        modifications["stability_weight"] = "+3%"
    elif any(w in answer_lower for w in ["unstable", "shift", "change", "fluid"]):
        modifications["stability_weight"] = "-3%"

    if "remember" in answer_lower or "forget" in answer_lower:
        if "less" in answer_lower or "slower" in answer_lower:
            modifications["memory_decay"] = "remember more"
        else:
            modifications["memory_decay"] = "forget more"

    return modifications


def summarize_answer(answer: str) -> str:
    """Create brief summary for graph display."""
    if not answer:
        return "No reflection"

    sentences = answer.replace(".", " ").split()
    if len(sentences) > 8:
        return " ".join(sentences[:8]) + "..."
    return answer[:60] + "..." if len(answer) > 60 else answer
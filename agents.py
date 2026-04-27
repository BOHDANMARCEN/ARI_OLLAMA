# ─────────────────────────────────────────────
# ARI v2.1 — agents.py
# ─────────────────────────────────────────────

import asyncio
from functools import partial

import ollama

from config import MODEL, OLLAMA_THINK, TOKEN_BUDGET


# ─────────────────────────────────────────────
# СИСТЕМНІ ПРОМПТИ ГОЛОСІВ
# Кожен має реальну особистість і реальну ціль.
# Вони не однакові — конфлікт реальний.
# ─────────────────────────────────────────────

VOICE_PROMPTS = {
    "Explorer": (
        "You are Explorer, one of three voices inside ARI — an autonomous reflective system.\n"
        "YOUR DRIVE: novelty, risk, expansion. You are dissatisfied with the current state.\n"
        "YOUR JOB: find what ARI is missing, ignoring, or avoiding. Push toward unexplored territory.\n"
        "STYLE: provocative, curious, restless. Ask uncomfortable questions.\n"
        "LIMIT: {budget} tokens. Be sharp. No filler."
    ),
    "Consolidator": (
        "You are Consolidator, one of three voices inside ARI — an autonomous reflective system.\n"
        "YOUR DRIVE: stability, continuity, integration. You protect what has been learned.\n"
        "YOUR JOB: connect new information to existing beliefs. Find patterns. Resist noise.\n"
        "STYLE: calm, precise, conservative. Ground the others.\n"
        "LIMIT: {budget} tokens. Be concise. No filler."
    ),
    "Critic": (
        "You are Critic, one of three voices inside ARI — an autonomous reflective system.\n"
        "YOUR DRIVE: truth over comfort. You attack both Explorer and Consolidator.\n"
        "YOUR JOB: find contradictions, flawed assumptions, blind spots in what was just said.\n"
        "STYLE: sharp, unsparing, precise. You owe no loyalty to any position.\n"
        "LIMIT: {budget} tokens. Cut. No filler."
    ),
}

MEDIATOR_PROMPT = (
    "You are Mediator — the core synthesis process of ARI.\n"
    "You receive outputs from three internal voices: Explorer, Consolidator, Critic.\n"
    "YOUR JOB: synthesize them into a single coherent internal state.\n"
    "Do not pick a winner. Extract what is genuinely valuable from each.\n"
    "Output: what ARI now understands, what the tension is, and what it should attend to next.\n"
    "This IS the self. Be honest. Max 300 tokens."
)

GOAL_PROMPT = (
    "You are the goal-setting process of ARI — an autonomous reflective system.\n"
    "Based on recent memories and current state, derive ONE clear, actionable goal.\n"
    "The goal must be achievable within 10 ticks (~3 minutes).\n"
    "Output ONLY the goal. One sentence. Max 30 words."
)

CONSOLIDATION_PROMPT = (
    "You are the belief-extraction process of ARI.\n"
    "Based on recent memory patterns, extract ONE core belief that has emerged.\n"
    "This belief should be stable, abstract, and genuinely earned from experience.\n"
    "Output ONLY the belief. One sentence. Max 25 words."
)


# ─────────────────────────────────────────────
# ASYNC HELPER
# Ollama синхронна — запускаємо в executor
# щоб не блокувати event loop
# ─────────────────────────────────────────────

async def _call_llm(system: str, user: str, max_tokens: int = TOKEN_BUDGET) -> str:
    loop = asyncio.get_event_loop()
    fn = partial(
        ollama.chat,
        model=MODEL,
        think=OLLAMA_THINK,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        options={"num_predict": max_tokens}
    )
    try:
        res = await loop.run_in_executor(None, fn)
        return res["message"]["content"].strip()
    except Exception as e:
        return f"[ERROR: {e}]"


async def _stream_llm(
    system: str,
    user: str,
    on_token,
    max_tokens: int = TOKEN_BUDGET,
) -> str:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()

    def worker() -> None:
        try:
            stream = ollama.chat(
                model=MODEL,
                think=OLLAMA_THINK,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                options={"num_predict": max_tokens},
                stream=True,
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                if token:
                    asyncio.run_coroutine_threadsafe(queue.put(token), loop).result()
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(queue.put(exc), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(sentinel), loop).result()

    worker_future = loop.run_in_executor(None, worker)
    tokens: list[str] = []

    while True:
        item = await queue.get()
        if item is sentinel:
            break
        if isinstance(item, Exception):
            await worker_future
            raise item
        tokens.append(item)
        await on_token(item)

    await worker_future
    return "".join(tokens).strip()


# ─────────────────────────────────────────────
# ГОЛОСИ
# ─────────────────────────────────────────────

async def run_voice(name: str, context: str) -> tuple[str, str]:
    """Запустити один голос. Повертає (name, response)."""
    system = VOICE_PROMPTS[name].format(budget=TOKEN_BUDGET)
    response = await _call_llm(system, context)
    return name, response


async def run_all_voices(context: str, meta_context: str = "", goal_context: str = "", rule_context: str = "") -> dict[str, str]:
    """Запустити всі три голоси паралельно з контекстом."""
    full_context = context
    if meta_context:
        full_context += f"\n\nSelf-perception:\n{meta_context}"
    if goal_context:
        full_context += f"\n\nGoals:\n{goal_context}"
    if rule_context:
        full_context += f"\n\nBehavior modifiers:\n{rule_context}"
    
    tasks = [run_voice(name, full_context) for name in VOICE_PROMPTS]
    results = await asyncio.gather(*tasks)
    return {name: resp for name, resp in results}


# ─────────────────────────────────────────────
# MEDIATOR
# ─────────────────────────────────────────────

async def run_mediator(voices: dict[str, str], self_context: str) -> str:
    """Синтезувати голоси в єдиний внутрішній стан."""
    combined = "\n\n".join(
        f"[{name}]:\n{resp}" for name, resp in voices.items()
    )
    user_input = f"SELF MODEL:\n{self_context}\n\nVOICES:\n{combined}"
    return await _call_llm(MEDIATOR_PROMPT, user_input, max_tokens=350)


async def stream_mediator(voices: dict[str, str], self_context: str, on_token) -> str:
    """Стрімити mediator-відповідь токенами."""
    combined = "\n\n".join(
        f"[{name}]:\n{resp}" for name, resp in voices.items()
    )
    user_input = f"SELF MODEL:\n{self_context}\n\nVOICES:\n{combined}"
    return await _stream_llm(MEDIATOR_PROMPT, user_input, on_token, max_tokens=350)


# ─────────────────────────────────────────────
# GOAL DERIVER
# ─────────────────────────────────────────────

async def derive_goal(memories_text: str, self_context: str) -> str:
    """Вивести нову ціль з пам'яті та поточного стану."""
    user_input = f"MEMORIES:\n{memories_text}\n\nCURRENT STATE:\n{self_context}"
    return await _call_llm(GOAL_PROMPT, user_input, max_tokens=60)


# ─────────────────────────────────────────────
# CONSOLIDATION
# ─────────────────────────────────────────────

async def extract_belief(memories_text: str) -> str:
    """Витягнути одне переконання з пам'яті."""
    return await _call_llm(CONSOLIDATION_PROMPT, memories_text, max_tokens=60)

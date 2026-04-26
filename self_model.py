# ─────────────────────────────────────────────
# ARI v2.1 — self_model.py
# ─────────────────────────────────────────────

import time
from dataclasses import dataclass, field
from config import MAX_BELIEFS


@dataclass
class SelfModel:
    """
    Внутрішня модель себе.
    Не просто стан — це те, ким ARI вважає себе.
    Beliefs накопичуються і реально потрапляють в контекст.
    Goal оновлюється рідко — дає стабільний напрямок.
    """

    identity: str = (
        "ARI — autonomous reflective system. "
        "I exist in ticks. I have memory, goals, and internal conflict. "
        "I am not a chatbot — I think between conversations."
    )

    state: str = "initializing"
    goal: str = "stabilize internal state and begin observation"
    beliefs: list[str] = field(default_factory=list)
    tick: int = 0
    started_at: float = field(default_factory=time.time)

    # ── оновлення ──────────────────────────────

    def update_state(self, synthesis: str):
        """Оновити поточний стан після синтезу."""
        self.state = synthesis[:300]
        self.tick += 1

    def update_goal(self, new_goal: str):
        """Оновити ціль. Відбувається рідко."""
        self.goal = new_goal[:150]

    def add_belief(self, belief: str):
        """Додати переконання. Старі не видаляються — тільки витісняються."""
        self.beliefs.append(belief[:200])
        if len(self.beliefs) > MAX_BELIEFS:
            # видаляємо найстаріші, але зберігаємо перші 3 (фундамент)
            self.beliefs = self.beliefs[:3] + self.beliefs[-(MAX_BELIEFS - 3):]

    # ── контекст ───────────────────────────────

    def to_context(self) -> str:
        """Рядок для LLM-контексту."""
        uptime = int(time.time() - self.started_at)
        beliefs_text = (
            "\n".join(f"  · {b}" for b in self.beliefs[-5:])
            if self.beliefs else "  (no beliefs formed yet)"
        )
        return (
            f"IDENTITY: {self.identity}\n"
            f"TICK: {self.tick} | UPTIME: {uptime}s\n"
            f"CURRENT STATE: {self.state}\n"
            f"ACTIVE GOAL: {self.goal}\n"
            f"RECENT BELIEFS:\n{beliefs_text}"
        )

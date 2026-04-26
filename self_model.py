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
    state_vector: dict[str, float] = field(default_factory=lambda: {
        "stability": 0.55,
        "novelty": 0.55,
        "confidence": 0.45,
        "coherence": 0.50,
    })
    tick: int = 0
    started_at: float = field(default_factory=time.time)

    # ── оновлення ──────────────────────────────

    def update_state(
        self,
        synthesis: str,
        voices: dict[str, str] | None = None,
        had_user_input: bool = False,
    ):
        """Оновити поточний стан після синтезу."""
        self.state = synthesis[:300]
        self._update_state_vector(synthesis, voices or {}, had_user_input)
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

    def snapshot(self) -> dict:
        uptime = int(time.time() - self.started_at)
        return {
            "identity": self.identity,
            "state": self.state,
            "goal": self.goal,
            "beliefs": self.beliefs[-8:],
            "tick": self.tick,
            "uptime": uptime,
            "state_vector": self.state_vector,
        }

    def export_graph_state(self, voices: dict[str, str] | None = None) -> dict:
        """Export brain state for force graph visualization."""
        nodes = [
            {"id": "Explorer", "group": "voice", "value": 15},
            {"id": "Consolidator", "group": "voice", "value": 15},
            {"id": "Critic", "group": "voice", "value": 15},
            {"id": "Mediator", "group": "core", "value": 25},
            {"id": "Self", "group": "core", "value": 30},
        ]

        links = [
            {"source": "Explorer", "target": "Mediator"},
            {"source": "Consolidator", "target": "Mediator"},
            {"source": "Critic", "target": "Mediator"},
            {"source": "Mediator", "target": "Self"},
        ]

        voice_texts = voices or {}
        for name, text in voice_texts.items():
            if text and len(text) > 10:
                thought_id = f"Thought_{name}_{self.tick}"
                nodes.append({
                    "id": thought_id,
                    "group": "thought",
                    "value": 5,
                    "label": name,
                    "text": text[:80],
                })
                links.append({"source": name, "target": thought_id})

        if self.goal:
            nodes.append({
                "id": "Goal",
                "group": "goal",
                "value": 20,
                "text": self.goal[:60],
            })
            links.append({"source": "Self", "target": "Goal"})

        for i, belief in enumerate(self.beliefs[-5:]):
            belief_id = f"Belief_{i}"
            nodes.append({
                "id": belief_id,
                "group": "belief",
                "value": 8,
                "text": belief[:60],
            })
            links.append({"source": "Self", "target": belief_id})

        for key, val in self.state_vector.items():
            metric_id = f"Metric_{key}"
            nodes.append({
                "id": metric_id,
                "group": "metric",
                "value": int(val * 10) + 5,
                "text": f"{key}: {val:.2f}",
            })
            links.append({"source": "Self", "target": metric_id})

        return {"nodes": nodes, "links": links}

    def _update_state_vector(
        self,
        synthesis: str,
        voices: dict[str, str],
        had_user_input: bool,
    ) -> None:
        critic_text = (voices.get("Critic") or "").lower()
        explorer_text = voices.get("Explorer") or ""
        consolidator_text = voices.get("Consolidator") or ""

        novelty_delta = 0.04 if explorer_text else -0.02
        stability_delta = 0.05 if consolidator_text else -0.03
        confidence_delta = 0.03 if len(synthesis) > 120 else -0.02
        coherence_delta = 0.04 if self.goal and len(synthesis) > 90 else -0.03

        if had_user_input:
            novelty_delta += 0.03
            confidence_delta += 0.02
        if any(term in critic_text for term in ("contradiction", "inconsistent", "flawed", "blind spot")):
            stability_delta -= 0.05
            coherence_delta -= 0.04
        if self.beliefs:
            confidence_delta += min(0.06, len(self.beliefs) * 0.01)
            coherence_delta += 0.02

        self.state_vector = {
            "stability": self._clamp(self.state_vector["stability"] + stability_delta),
            "novelty": self._clamp(self.state_vector["novelty"] + novelty_delta),
            "confidence": self._clamp(self.state_vector["confidence"] + confidence_delta),
            "coherence": self._clamp(self.state_vector["coherence"] + coherence_delta),
        }

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, round(value, 3)))

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
            f"STATE VECTOR: {self.state_vector}\n"
            f"RECENT BELIEFS:\n{beliefs_text}"
        )

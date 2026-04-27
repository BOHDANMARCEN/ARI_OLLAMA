# ─────────────────────────────────────────────
# ARI v2.1 — self_model.py
# ─────────────────────────────────────────────

import time
from dataclasses import dataclass, field
from config import MAX_BELIEFS


@dataclass
class Belief:
    """Simple belief representation for export."""
    text: str
    strength: float = 1.0


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
    identity_vector: dict[str, float] = field(default_factory=lambda: {
        "stability": 0.5,
        "curiosity": 0.5,
        "aggression": 0.3,
    })
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
            self.beliefs = self.beliefs[:3] + self.beliefs[-(MAX_BELIEFS - 3):]
        self._update_identity_vector()

    def _update_identity_vector(self) -> None:
        """Update identity vector based on beliefs."""
        if not self.beliefs:
            return
        total = len(self.beliefs)
        avg_len = sum(len(b) for b in self.beliefs) / total
        reinforced = sum(1 for b in self.beliefs if len(b) > 30)
        
        stability = min(1.0, 0.3 + (reinforced / total) * 0.4)
        curiosity = max(0.1, 0.8 - stability * 0.5)
        aggression = abs(curiosity - stability) * 0.5
        
        self.identity_vector = {
            "stability": round(stability, 3),
            "curiosity": round(curiosity, 3),
            "aggression": round(min(1.0, aggression), 3),
        }

    def update_identity_from_belief_system(self, belief_system) -> None:
        """Update identity vector from external BeliefSystem."""
        self.identity_vector = belief_system.get_identity_vector()
        
        for belief in belief_system.top(5):
            if belief.text not in self.beliefs:
                self.add_belief(belief.text)

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

    def _score_power(self, text: str, keywords: list[str]) -> float:
        """Score voice power based on keyword presence."""
        if not text:
            return 0.0
        text_lower = text.lower()
        score = sum(0.3 for kw in keywords if kw in text_lower)
        score += 0.2 * min(1.0, len(text) / 200)
        return round(score + 0.2, 3)

    def export_graph_state(self, voices: dict[str, str] | None = None, memories: list[dict] | None = None, belief_system=None, crisis_engine=None, self_observer=None, goal_system=None) -> dict:
        """Export brain state for force graph visualization with live metrics."""
        voice_texts = voices or {}

        if belief_system:
            from crisis_engine import detect_conflicts
            belief_list = belief_system.get_all()
            conflicts = detect_conflicts(belief_list)
        else:
            belief_list = []
            conflicts = []

        meta_state = None
        meta_beliefs = []
        if self_observer:
            meta_state = self_observer.get_state()
            meta_beliefs = self_observer.get_top_meta_beliefs(3)

        goal_state = None
        goal_nodes = []
        if goal_system:
            goal_state = goal_system.get_state()
            goal_nodes = goal_system.get_top_goals(3)

        explorer_text = voice_texts.get("Explorer", "")
        critic_text = voice_texts.get("Critic", "")
        consolidator_text = voice_texts.get("Consolidator", "")

        explorer_power = self._score_power(explorer_text, ["new", "risk", "explore", "unknown", "change", "push", "try"])
        critic_power = self._score_power(critic_text, ["error", "flaw", "contradiction", "problem", "issue", "wrong", "weak"])
        consolidator_power = self._score_power(consolidator_text, ["stable", "keep", "continue", "pattern", "integrate", "connect"])

        coherence = round(0.5 + (consolidator_power * 0.3) - (abs(explorer_power - critic_power) * 0.2), 3)
        coherence = max(0.1, min(1.0, coherence))

        conflict = round(abs(explorer_power - consolidator_power) + (critic_power * 0.5), 3)

        entropy = round(0.3 + (explorer_power * 0.3) + (critic_power * 0.2) + (1 - coherence) * 0.2, 3)
        entropy = max(0.1, min(1.0, entropy))

        x_bias = round((explorer_power - critic_power) * 0.15, 3)
        y_bias = round((consolidator_power - explorer_power) * 0.1 + (self.state_vector.get("stability", 0.5) - 0.5) * 0.1, 3)

        nodes = [
            {"id": "Explorer", "group": "voice", "value": 8 + explorer_power * 5, "power": explorer_power},
            {"id": "Critic", "group": "voice", "value": 8 + critic_power * 5, "power": critic_power},
            {"id": "Consolidator", "group": "voice", "value": 8 + consolidator_power * 5, "power": consolidator_power},
            {"id": "Mediator", "group": "core", "value": 18, "xBias": x_bias, "yBias": y_bias},
            {"id": "Self", "group": "core", "value": 22, "xBias": x_bias * 0.5, "yBias": y_bias * 0.5},
        ]

        links = [
            {"source": "Explorer", "target": "Mediator", "strength": 0.3 + explorer_power * 0.7},
            {"source": "Critic", "target": "Mediator", "strength": 0.3 + critic_power * 0.7},
            {"source": "Consolidator", "target": "Mediator", "strength": 0.3 + consolidator_power * 0.7},
            {"source": "Mediator", "target": "Self", "strength": 0.8},
            {"source": "Self", "target": "Identity", "strength": 0.7},
        ]

        nodes.append({
            "id": "Identity",
            "group": "identity",
            "value": 16,
            "xBias": x_bias * 0.3,
            "yBias": y_bias * 0.3,
        })

        for name, text in voice_texts.items():
            if text and len(text) > 10:
                thought_id = f"Thought_{name}_{self.tick}"
                nodes.append({
                    "id": thought_id,
                    "group": "thought",
                    "value": 4 + len(text) / 100,
                    "label": name,
                    "text": text[:60],
                })
                links.append({"source": name, "target": thought_id, "strength": 0.4})

        memory_list = memories or []
        for i, mem in enumerate(memory_list[:5]):
            mem_id = f"mem_{i}"
            mem_weight = mem.get("weight", 0.5) if isinstance(mem, dict) else 0.5
            nodes.append({
                "id": mem_id,
                "group": "memory",
                "value": 3 + min(7, mem_weight * 10),
                "text": mem.get("text", "")[:50] if isinstance(mem, dict) else str(mem)[:50],
            })
            links.append({
                "source": mem_id,
                "target": "Mediator",
                "strength": 0.2 + mem_weight * 0.5,
            })

        if self.goal:
            nodes.append({
                "id": "Goal",
                "group": "goal",
                "value": 12,
                "text": self.goal[:50],
            })
            links.append({"source": "Self", "target": "Goal", "strength": 0.6})

        belief_export = belief_list if belief_list else [Belief(b, 1.0) for b in self.beliefs[-4:]]
        for i, belief in enumerate(belief_export[:4]):
            belief_id = f"Belief_{i}"
            if hasattr(belief, 'strength'):
                belief_strength = belief.strength
                belief_text = belief.text
            else:
                belief_strength = 1.0
                belief_text = str(belief)
            nodes.append({
                "id": belief_id,
                "group": "belief",
                "value": 4 + min(4, belief_strength),
                "text": belief_text[:45],
            })
            links.append({"source": "Identity", "target": belief_id, "strength": 0.2 + belief_strength * 0.3})

        for i, (b1, b2) in enumerate(conflicts[:3]):
            conflict_id = f"Conflict_{i}"
            b1_text = getattr(b1, 'text', str(b1))[:25]
            b2_text = getattr(b2, 'text', str(b2))[:25]
            nodes.append({
                "id": conflict_id,
                "group": "conflict",
                "value": 7,
                "text": f"{b1_text} ↔ {b2_text}",
            })
            links.append({"source": conflict_id, "target": "Identity", "strength": 0.6})

        crisis_state = crisis_engine.get_state() if crisis_engine else {"active": False, "intensity": 0.0}

        nodes.append({
            "id": "SelfModel",
            "group": "meta",
            "value": 16,
        })
        links.append({"source": "Identity", "target": "SelfModel", "strength": 0.7})

        for i, mb in enumerate(meta_beliefs):
            meta_id = f"Meta_{i}"
            mb_text = mb.text if hasattr(mb, 'text') else str(mb)
            mb_weight = mb.weight if hasattr(mb, 'weight') else 1.0
            nodes.append({
                "id": meta_id,
                "group": "meta",
                "value": 4 + min(4, mb_weight * 3),
                "text": mb_text[:40],
            })
            links.append({"source": meta_id, "target": "SelfModel", "strength": 0.4})

        for i, goal in enumerate(goal_nodes):
            goal_id = f"Goal_{i}"
            goal_text = goal.text if hasattr(goal, 'text') else str(goal)
            goal_prog = goal.progress if hasattr(goal, 'progress') else 0.0
            nodes.append({
                "id": goal_id,
                "group": "goal",
                "value": 6 + min(6, goal.priority * 4) if hasattr(goal, 'priority') else 6,
                "text": f"{goal_text[:35]} ({goal_prog:.0%})",
            })
            links.append({"source": "SelfModel", "target": goal_id, "strength": 0.5})

        for key, val in self.state_vector.items():
            metric_id = f"Metric_{key}"
            nodes.append({
                "id": metric_id,
                "group": "metric",
                "value": 3 + int(val * 8),
                "text": f"{key}: {val:.2f}",
            })
            links.append({"source": "Self", "target": metric_id, "strength": 0.3})

        return {
            "nodes": nodes,
            "links": links,
            "meta": {
                "coherence": coherence,
                "conflict": conflict,
                "entropy": entropy,
                "tick": self.tick,
                "identity": self.identity_vector,
                "crisis": crisis_state,
                "self": meta_state,
                "goal": goal_state,
            },
        }

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

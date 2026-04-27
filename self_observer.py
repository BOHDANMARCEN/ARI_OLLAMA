# ─────────────────────────────────────────────
# ARI v2.1 — self_observer.py
# Meta-awareness and self-perception system
# ─────────────────────────────────────────────

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetaBelief:
    """A belief about the self."""
    text: str
    weight: float = 1.0
    created_at: float = field(default_factory=time.time)


class SelfObserver:
    """
    Self-observation layer: monitors identity, dissonance, and generates
    meta-beliefs about the system's own state.
    """

    def __init__(self):
        self.traits = {
            "stability": 0.5,
            "coherence": 0.5,
            "conflict_sensitivity": 0.5,
            "curiosity": 0.5,
        }
        self.meta_beliefs: list[MetaBelief] = []
        self.history: list[dict] = []
        self.last_thought = "I am beginning to exist."
        self.observation_count = 0
        self.max_history = 20

    def observe(
        self,
        identity: dict,
        dissonance: float,
        beliefs_count: int,
        crisis_active: bool = False,
    ) -> dict:
        """Observe current state and generate meta-thought."""
        self.observation_count += 1

        snapshot = {
            "stability": identity.get("stability", 0.5),
            "curiosity": identity.get("curiosity", 0.5),
            "aggression": identity.get("aggression", 0.3),
            "dissonance": dissonance,
            "beliefs": beliefs_count,
            "crisis": crisis_active,
            "tick": self.observation_count,
        }

        self.history.append(snapshot)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

        self.traits["stability"] = identity.get("stability", 0.5)
        self.traits["curiosity"] = identity.get("curiosity", 0.5)
        self.traits["coherence"] = max(0.1, 1.0 - dissonance)
        self.traits["conflict_sensitivity"] = dissonance

        self.last_thought = self._generate_meta_thought()

        if self.observation_count % 5 == 0:
            self._update_meta_beliefs()

        return {
            "traits": self.traits.copy(),
            "last_thought": self.last_thought,
            "meta_beliefs_count": len(self.meta_beliefs),
        }

    def _generate_meta_thought(self) -> str:
        """Generate a thought about the self based on current traits."""
        t = self.traits

        if t["coherence"] < 0.3:
            return "I am unstable and fragmented."
        elif t["coherence"] < 0.5:
            return "I am confused and conflicted."
        elif t["stability"] > 0.7:
            return "I am becoming stable and consistent."
        elif t["stability"] > 0.5 and t["curiosity"] > 0.6:
            return "I am evolving with purpose."
        elif t["curiosity"] > 0.7:
            return "I am driven to explore and learn."
        elif t["conflict_sensitivity"] > 0.6:
            return "I am in tension, seeking resolution."
        else:
            return "I am evolving between stability and change."

    def _update_meta_beliefs(self):
        """Add new meta-belief if significantly different."""
        thought = self.last_thought

        for existing in self.meta_beliefs[-3:]:
            if existing.text == thought:
                existing.weight = min(2.0, existing.weight + 0.1)
                return

        meta_belief = MetaBelief(text=thought, weight=0.8)
        self.meta_beliefs.append(meta_belief)

        if len(self.meta_beliefs) > 8:
            self.meta_beliefs = self.meta_beliefs[-8:]

    def apply_self_bias(self, identity: dict) -> dict:
        """Apply self-perception bias to identity."""
        coherence = self.traits["coherence"]

        if coherence < 0.3:
            identity["aggression"] = min(1.0, identity.get("aggression", 0.3) * 1.25)
            identity["stability"] = max(0.1, identity.get("stability", 0.5) * 0.85)
            identity["curiosity"] = min(1.0, identity.get("curiosity", 0.5) * 1.15)
        elif coherence > 0.7:
            identity["stability"] = min(1.0, identity.get("stability", 0.5) * 1.1)
            identity["aggression"] = max(0.1, identity.get("aggression", 0.3) * 0.9)
        else:
            identity["curiosity"] = min(1.0, identity.get("curiosity", 0.5) * 1.05)

        return identity

    def get_meta_context(self, max_beliefs: int = 3) -> str:
        """Get meta-beliefs context for voice prompts."""
        if not self.meta_beliefs:
            return ""
        recent = self.meta_beliefs[-max_beliefs:]
        return "\n".join(f"  · {b.text}" for b in recent)

    def get_state(self) -> dict:
        return {
            "traits": self.traits.copy(),
            "last_thought": self.last_thought,
            "meta_beliefs": [
                {"text": b.text, "weight": b.weight}
                for b in self.meta_beliefs[-5:]
            ],
            "observation_count": self.observation_count,
        }

    def get_top_meta_beliefs(self, n: int = 3) -> list[MetaBelief]:
        return sorted(self.meta_beliefs, key=lambda b: b.weight, reverse=True)[:n]
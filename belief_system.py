# ─────────────────────────────────────────────
# ARI v2.1 — belief_system.py
# Belief System with reinforcement and decay
# ─────────────────────────────────────────────

import time
import re
from typing import Any


class Belief:
    def __init__(self, text: str, strength: float = 1.0):
        self.text = text
        self.strength = strength
        self.age = 0
        self.reinforced = 1
        self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "strength": self.strength,
            "age": self.age,
            "reinforced": self.reinforced,
        }


class BeliefSystem:
    """
    Belief system with aging, decay, and reinforcement.
    Beliefs can be extracted from synthesis and reinforced over time.
    """

    BELIEF_PATTERNS = [
        r"I am (\w+)",
        r"I believe (\w+)",
        r"I must (\w+)",
        r"I need to (\w+)",
        r"My purpose is (\w+)",
        r"I will (\w+)",
        r"I should (\w+)",
        r"I (?:always|never) (\w+)",
        r"the way (\w+)",
        r"the truth is (\w+)",
    ]

    def __init__(self, max_beliefs: int = 12):
        self.beliefs: list[Belief] = []
        self.max_beliefs = max_beliefs

    def add(self, text: str, strength: float = 1.0) -> None:
        clean_text = text.strip()[:150]
        if not clean_text:
            return

        for existing in self.beliefs:
            if self._similar(clean_text, existing.text):
                existing.strength = min(3.0, existing.strength + 0.2)
                existing.reinforced += 1
                return

        belief = Belief(clean_text, strength)
        self.beliefs.append(belief)

        if len(self.beliefs) > self.max_beliefs:
            self._prune_weakest()

    def update(self) -> None:
        for belief in self.beliefs:
            belief.age += 1
            decay = 0.98 ** belief.age
            belief.strength = max(0.1, belief.strength * decay)

    def reinforce(self, text: str) -> None:
        text_lower = text.lower()
        for belief in self.beliefs:
            if belief.text.lower() in text_lower:
                belief.strength = min(3.0, belief.strength * 1.15)
                belief.reinforced += 1

    def top(self, n: int = 5) -> list[Belief]:
        sorted_beliefs = sorted(self.beliefs, key=lambda b: b.strength, reverse=True)
        return sorted_beliefs[:n]

    def get_all(self) -> list[Belief]:
        return self.beliefs

    def get_identity_vector(self) -> dict[str, float]:
        if not self.beliefs:
            return {"stability": 0.5, "curiosity": 0.5, "aggression": 0.5}

        total_strength = sum(b.strength for b in self.beliefs)
        avg_strength = total_strength / len(self.beliefs)

        reinforced_count = sum(1 for b in self.beliefs if b.reinforced > 1)
        reinforcement_ratio = reinforced_count / len(self.beliefs)

        stability = min(1.0, avg_strength / 3)
        curiosity = max(0.1, 1.0 - stability * 0.7)
        aggression = abs(curiosity - stability) * reinforcement_ratio

        return {
            "stability": round(stability, 3),
            "curiosity": round(curiosity, 3),
            "aggression": round(min(1.0, aggression), 3),
        }

    def extract_from_text(self, text: str) -> list[str]:
        beliefs = []
        text_lower = text.lower()

        for pattern in self.BELIEF_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if len(match) > 3:
                    beliefs.append(match.strip())

        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 120:
                if any(kw in sentence.lower() for kw in ["must", "need", "will", "should", "always", "never"]):
                    beliefs.append(sentence)

        return list(set(beliefs))[:3]

    def _similar(self, text1: str, text2: str) -> bool:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1 & words2
        union = words1 | words2
        if not union:
            return False
        return len(intersection) / len(union) > 0.5

    def _prune_weakest(self) -> None:
        if len(self.beliefs) <= self.max_beliefs:
            return
        sorted_beliefs = sorted(self.beliefs, key=lambda b: b.strength)
        self.beliefs = sorted_beliefs[-self.max_beliefs:]

    def to_export(self) -> list[dict[str, Any]]:
        return [b.to_dict() for b in self.beliefs]
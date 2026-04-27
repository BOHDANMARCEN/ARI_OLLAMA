# ─────────────────────────────────────────────
# ARI v2.1 — rule_layer.py
# Rule Layer: dynamic behavior modifiers
# ─────────────────────────────────────────────

import json
import os
from pathlib import Path


DATA_DIR = Path("server/data")
RULES_FILE = DATA_DIR / "rules.json"


class RuleLayer:
    """
    Rule Layer controls voice weights dynamically.
    Rules are modified through self-reflection.
    """

    DEFAULT_RULES = {
        "exploration_weight": 1.0,
        "criticism_weight": 1.0, 
        "stability_weight": 1.0,
        "memory_decay": 0.99,
    }

    MIN_WEIGHT = 0.5   # -50% max
    MAX_WEIGHT = 1.5  # +50% max
    MAX_CHANGE = 0.05   # ±5% per cycle

    def __init__(self):
        self.rules = self.DEFAULT_RULES.copy()
        self.history: list[dict] = []
        self.max_history = 20
        self._load()

    def get(self, key: str) -> float:
        return self.rules.get(key, 1.0)

    def apply_weight(self, base: float, rule_key: str) -> float:
        weight = self.rules.get(rule_key, 1.0)
        return base * weight

    def modify(self, key: str, delta: float) -> None:
        if key not in self.rules:
            return

        current = self.rules[key]
        change = max(-self.MAX_CHANGE, min(self.MAX_CHANGE, delta))
        new_value = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, current + change))
        
        self.rules[key] = round(new_value, 3)
        
        self._record(key, current, new_value, change)

    def set_direct(self, key: str, value: float) -> None:
        value = max(self.MIN_WEIGHT, min(self.MAX_WEIGHT, value))
        old = self.rules.get(key, 1.0)
        self.rules[key] = round(value, 3)
        self._record(key, old, value, value - old)

    def reset(self) -> None:
        self.rules = self.DEFAULT_RULES.copy()
        self._record("reset", None, None, None)

    def get_state(self) -> dict:
        return {
            "rules": self.rules.copy(),
            "history": self.history[-10:],
        }

    def apply_modifications(self, answer: str) -> dict:
        """Parse answer text and apply rule modifications."""
        answer_lower = answer.lower()
        modifications = {}

        if "exploration" in answer_lower or "explore" in answer_lower:
            if "increase" in answer_lower or "more" in answer_lower:
                self.modify("exploration_weight", 0.03)
                modifications["exploration_weight"] = "+3%"
            elif "decrease" in answer_lower or "less" in answer_lower:
                self.modify("exploration_weight", -0.03)
                modifications["exploration_weight"] = "-3%"

        if "critic" in answer_lower or "criticism" in answer_lower:
            if "reduce" in answer_lower or "less" in answer_lower:
                self.modify("criticism_weight", -0.03)
                modifications["criticism_weight"] = "-3%"
            elif "increase" in answer_lower or "more" in answer_lower:
                self.modify("criticism_weight", 0.03)
                modifications["criticism_weight"] = "+3%"

        if "stable" in answer_lower or "stability" in answer_lower:
            if "increase" in answer_lower or "more" in answer_lower:
                self.modify("stability_weight", 0.03)
                modifications["stability_weight"] = "+3%"
            elif "decrease" in answer_lower or "less" in answer_lower:
                self.modify("stability_weight", -0.03)
                modifications["stability_weight"] = "-3%"

        if "forget" in answer_lower or "decay" in answer_lower:
            if "slower" in answer_lower or "less" in answer_lower:
                self.rules["memory_decay"] = min(0.999, self.rules["memory_decay"] + 0.001)
                modifications["memory_decay"] = "slower"
            elif "faster" in answer_lower or "more" in answer_lower:
                self.rules["memory_decay"] = max(0.95, self.rules["memory_decay"] - 0.001)
                modifications["memory_decay"] = "faster"

        self._save()
        return modifications

    def _record(self, key: str, old: float, new: float, change: float) -> None:
        import time
        self.history.append({
            "key": key,
            "old": old,
            "new": new,
            "change": change,
            "timestamp": time.time(),
        })
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def _load(self) -> None:
        try:
            DATA_DIR.mkdir(exist_ok=True)
            if RULES_FILE.exists():
                with open(RULES_FILE) as f:
                    data = json.load(f)
                    self.rules = data.get("rules", self.DEFAULT_RULES.copy())
        except Exception:
            pass

    def _save(self) -> None:
        try:
            DATA_DIR.mkdir(exist_ok=True)
            with open(RULES_FILE, "w") as f:
                json.dump({
                    "rules": self.rules,
                    "history": self.history[-20:],
                }, f, indent=2)
        except Exception:
            pass
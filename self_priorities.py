# ─────────────────────────────────────────────
# ARI v9 — self_priorities.py
# Core values that guide decisions
# ─────────────────────────────────────────────


class SelfPriorities:
    """
    Not just goals — values that matter.
    truth, stability, growth, connection
    """

    def __init__(self):
        self.priorities = {
            "truth": 0.7,
            "stability": 0.6,
            "growth": 0.8,
            "connection": 0.5,
        }
        self.history: list[dict] = []
        self.max_history = 30

    def get_top(self) -> str:
        """Return name of highest priority."""
        return max(self.priorities, key=self.priorities.get)

    def get_ranked(self) -> list[tuple[str, float]]:
        """Return priorities sorted by value."""
        return sorted(self.priorities.items(), key=lambda x: x[1], reverse=True)

    def get_state(self) -> dict:
        return {
            "priorities": self.priorities.copy(),
            "top": self.get_top(),
            "ranked": self.get_ranked()[:3],
            "history": self.history[-10:],
        }

    def adjust(self, priority: str, delta: float) -> None:
        """Adjust priority value."""
        if priority not in self.priorities:
            return
        
        old = self.priorities[priority]
        self.priorities[priority] = max(0.1, min(1.0, old + delta))
        
        self._record(priority, old, self.priorities[priority])

    def influence_goal_choice(self, goals: list[dict]) -> list[dict]:
        """Bias goal selection based on priorities."""
        if not goals:
            return goals
        
        top_priorities = [p for p, v in self.get_ranked()[:2]]
        bias_text = ""
        
        if "growth" in top_priorities:
            bias_text += "prefer exploratory goals"
        if "stability" in top_priorities:
            bias_text += " prefer stable consistent goals"
        if "truth" in top_priorities:
            bias_text += " prefer analytical goals"
        
        return goals

    def get_influence_text(self) -> str:
        """Get text describing current influence."""
        top = self.get_top()
        ranked = self.get_ranked()[:3]
        return f"{top.capitalize()} > {' > '.join(r[0] for r in ranked[1:])}"

    def apply_to_context(self, context: str) -> str:
        """Add priority context to prompt."""
        top = self.get_top()
        ranked = self.get_ranked()
        
        text = f"\nCORE VALUES: "
        text += " | ".join(f"{p}:{v:.1f}" for p, v in ranked)
        text += f"\nTOP PRIORITY: {top}\n"
        
        return context + text

    def _record(self, key: str, old: float, new: float) -> None:
        import time
        self.history.append({
            "priority": key,
            "old": old,
            "new": new,
            "timestamp": time.time(),
        })
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
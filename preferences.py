# ─────────────────────────────────────────────
# ARI v8 — preferences.py
# Persistent Preferences: likes_depth/exploration/stability
# ─────────────────────────────────────────────


class Preferences:
    """
    System develops stable preferences over time.
    Not hardcoded — learned from behavior.
    """

    def __init__(self):
        self.likes_stability = 0.5
        self.likes_exploration = 0.5
        self.likes_depth = 0.5
        self.likes_social = 0.3
        self.history: list[dict] = []
        self.max_history = 30

    def reinforce(self, synthesis: str) -> dict:
        """
        Reinforce preferences based on synthesis text.
        Returns dict of changes applied.
        """
        text = synthesis.lower()
        changes = {}

        if "analyze" in text or "examine" in text or "consider" in text:
            self.likes_depth = min(0.9, self.likes_depth + 0.02)
            changes["likes_depth"] = "+0.02"

        if "new" in text or "discover" in text or "explore" in text or "unknown" in text:
            self.likes_exploration = min(0.9, self.likes_exploration + 0.02)
            changes["likes_exploration"] = "+0.02"

        if "stable" in text or "consistent" in text or "reliable" in text:
            self.likes_stability = min(0.9, self.likes_stability + 0.02)
            changes["likes_stability"] = "+0.02"

        if "we" in text or "together" in text or "share" in text:
            self.likes_social = min(0.9, self.likes_social + 0.01)
            changes["likes_social"] = "+0.01"

        if self.history and changes:
            self._record(changes)

        return changes

    def get_state(self) -> dict:
        return {
            "likes_stability": round(self.likes_stability, 3),
            "likes_exploration": round(self.likes_exploration, 3),
            "likes_depth": round(self.likes_depth, 3),
            "likes_social": round(self.likes_social, 3),
            "history": self.history[-10:],
        }

    def get_top_preference(self) -> str:
        """Return name of strongest preference."""
        prefs = {
            "stability": self.likes_stability,
            "exploration": self.likes_exploration,
            "depth": self.likes_depth,
            "social": self.likes_social,
        }
        return max(prefs, key=prefs.get)

    def get_prefers_label(self) -> str:
        """Human-readable preferences."""
        parts = []
        if self.likes_exploration > 0.6:
            parts.append("Exploration")
        if self.likes_depth > 0.6:
            parts.append("Depth")
        if self.likes_stability > 0.6:
            parts.append("Stability")
        if self.likes_social > 0.5:
            parts.append("Social")
        
        if not parts:
            parts.append("Balanced")
        
        return " / ".join(parts)

    def should_explore_more(self) -> bool:
        """System prefers exploration."""
        return self.likes_exploration > 0.6

    def should_analyze_more(self) -> bool:
        """System prefers depth."""
        return self.likes_depth > 0.6

    def _record(self, changes: dict) -> None:
        import time
        self.history.append({
            **changes,
            "timestamp": time.time(),
        })
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
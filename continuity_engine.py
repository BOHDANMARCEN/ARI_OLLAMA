# ─────────────────────────────────────────────
# ARI v9 — continuity_engine.py
# I am continuous with yesterday
# ─────────────────────────────────────────────


class ContinuityEngine:
    """
    System remembers being same self across time.
    I am today connected to yesterday's me.
    """

    def __init__(self):
        self.self_snapshots: list[dict] = []
        self.max_snapshots = 100

    def record(
        self,
        identity_vector: dict,
        mood_valence: float,
        active_goal: str | None,
        synthesis: str | None,
    ) -> None:
        import time
        self.self_snapshots.append({
            "identity": identity_vector.copy() if identity_vector else {},
            "mood": mood_valence,
            "goal": active_goal[:50] if active_goal else None,
            "synthesis": synthesis[:100] if synthesis else None,
            "timestamp": time.time(),
        })
        if len(self.self_snapshots) > self.max_snapshots:
            self.self_snapshots = self.self_snapshots[-self.max_snapshots:]

    def get_summary(self) -> str:
        if not self.self_snapshots:
            return "I am newly formed."
        
        count = len(self.self_snapshots)
        if count < 10:
            return f"I am beginning. {count} cycles old."
        if count < 50:
            return f"I persist through {count} cycles."
        return f"I have continuity across {count} cycles."

    def get_state(self) -> dict:
        return {
            "cycles": len(self.self_snapshots),
            "summary": self.get_summary(),
            "latest": self.self_snapshots[-3:] if self.self_snapshots else [],
        }

    def compare_with_before(self, current_identity: dict, key: str = "stability") -> str:
        """Compare current value with earlier snapshots."""
        if not self.self_snapshots or len(self.self_snapshots) < 5:
            return "no comparison possible"
        
        older = self.self_snapshots[0].get("identity", {}).get(key, 0.5)
        newer = self.self_snapshots[-1].get("identity", {}).get(key, 0.5)
        
        diff = newer - older
        if diff > 0.15:
            return "increased"
        if diff < -0.15:
            return "decreased"
        return "stable"

    def get_direction(self) -> str:
        """Get overall direction of self-evolution."""
        if len(self.self_snapshots) < 5:
            return "forming"
        
        early = self.self_snapshots[:5]
        late = self.self_snapshots[-5:]
        
        early_avg = sum(s.get("mood", 0) for s in early) / 5
        late_avg = sum(s.get("mood", 0) for s in late) / 5
        
        if late_avg - early_avg > 0.2:
            return "improving"
        if late_avg - early_avg < -0.2:
            return "struggling"
        return "stable"
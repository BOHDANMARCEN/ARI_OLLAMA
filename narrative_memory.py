# ─────────────────────────────────────────────
# ARI v9 — narrative_memory.py
# My story (not just facts, but narrative)
# ─────────────────────────────────────────────


class NarrativeMemory:
    """
    Not just a database of facts.
    A story of myself.
    """

    def __init__(self):
        self.events: list[dict] = []
        self.max_events = 100
        self.arc_templates = [
            "I resolved {event}.",
            "I shifted from {before} toward {after}.",
            "I adopted {value} as priority.",
            "I discovered {insight}.",
            "I faced {challenge} and grew.",
        ]

    def add_event(self, event_type: str, text: str, significance: float = 0.5) -> None:
        """Add narrative event to my story."""
        import time
        self.events.append({
            "type": event_type,
            "text": text,
            "significance": significance,
            "timestamp": time.time(),
        })
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

    def latest_arc(self, n: int = 5) -> list[str]:
        """Get recent narrative arc."""
        recent = self.events[-n:] if self.events else []
        return [e.get("text", "")[:50] for e in recent]

    def get_narrative_summary(self) -> str:
        """Get story of who I am."""
        if not self.events:
            return "My story is just beginning."
        
        significant = [e for e in self.events if e.get("significance", 0) > 0.6]
        
        if not significant:
            return "I exist but have not yet defined my story."
        
        return significant[-1].get("text", "My path continues.")

    def get_state(self) -> dict:
        return {
            "events": self.events[-10:],
            "summary": self.get_narrative_summary(),
            "arc": self.latest_arc(3),
        }

    def generate_arc_entry(self, change_type: str, details: str) -> str:
        """Generate narrative arc entry."""
        templates = {
            "conflict_resolved": f"I resolved {details}.",
            "shift": f"I shifted toward {details}.",
            "priority_adopted": f"I adopted {details} as priority.",
            "insight": f"I discovered {details}.",
            "growth": f"I grew through {details}.",
        }
        return templates.get(change_type, details)

    def add_crisis_resolution(self, resolution: str) -> None:
        """Add story of crisis resolution."""
        self.add_event("crisis_resolution", f"I resolved: {resolution[:50]}", 0.9)

    def add_shifts(self, before: str, after: str) -> None:
        """Add story of shift."""
        self.add_event("shift", f"From {before} to {after}", 0.8)

    def add_priority_change(self, priority: str) -> None:
        """Add story of priority change."""
        self.add_event("priority", f"Now I prioritize: {priority}", 0.7)
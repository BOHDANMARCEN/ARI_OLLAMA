# ─────────────────────────────────────────────
# ARI v2.1 — crisis_engine.py
# Conflict detection, cognitive dissonance, crisis mode
# ─────────────────────────────────────────────

from typing import Any


CONTRADICTIONS = [
    ("stable", "chaos"),
    ("stable", "disorder"),
    ("order", "risk"),
    ("order", "freedom"),
    ("control", "chaos"),
    ("control", "freedom"),
    ("safe", "danger"),
    ("safe", "risk"),
    ("predict", "uncertain"),
    ("certain", "doubt"),
    ("continue", "stop"),
    ("keep", "change"),
    ("accept", "reject"),
    ("believe", "doubt"),
    ("trust", "distrust"),
    ("peace", "conflict"),
    ("harmony", "tension"),
]


def belief_conflict(b1: dict | Any, b2: dict | Any) -> bool:
    """Check if two beliefs contain contradictory concepts."""
    if hasattr(b1, 'text'):
        t1 = b1.text.lower()
    else:
        t1 = str(b1).lower()
    
    if hasattr(b2, 'text'):
        t2 = b2.text.lower()
    else:
        t2 = str(b2).lower()

    for a, b in CONTRADICTIONS:
        if (a in t1 and b in t2) or (b in t1 and a in t2):
            return True

    words1 = set(t1.split())
    words2 = set(t2.split())
    common = words1 & words2
    if len(common) < 3:
        return False
    
    return False


def detect_conflicts(beliefs: list) -> list:
    """Detect all conflicts between beliefs."""
    conflicts = []
    
    for i in range(len(beliefs)):
        for j in range(i + 1, len(beliefs)):
            b1 = beliefs[i]
            b2 = beliefs[j]
            
            if belief_conflict(b1, b2):
                conflicts.append((b1, b2))
    
    return conflicts


def compute_dissonance(conflicts: list) -> float:
    """Compute cognitive dissonance from conflicts."""
    if not conflicts:
        return 0.0
    return min(1.0, len(conflicts) * 0.25)


class CrisisEngine:
    """Manages crisis state based on cognitive dissonance."""

    def __init__(self):
        self.active = False
        self.intensity = 0.0
        self.dissonance = 0.0
        self.trigger_count = 0

    def update(self, dissonance: float) -> dict:
        """Update crisis state based on dissonance level."""
        self.dissonance = dissonance
        
        was_active = self.active
        
        if dissonance > 0.6:
            self.active = True
            self.intensity = min(1.0, dissonance)
            self.trigger_count += 1
        elif dissonance < 0.3:
            self.active = False
            self.intensity = max(0.0, self.intensity - 0.1)
        
        return {
            "active": self.active,
            "intensity": self.intensity,
            "dissonance": self.dissonance,
            "triggered": self.active and not was_active,
        }

    def get_state(self) -> dict:
        return {
            "active": self.active,
            "intensity": self.intensity,
            "dissonance": self.dissonance,
            "trigger_count": self.trigger_count,
        }


def crisis_response(beliefs: list, max_remove: int = 1) -> list:
    """Remove weakest beliefs during crisis."""
    if not beliefs:
        return []
    
    sorted_beliefs = sorted(beliefs, key=lambda b: getattr(b, 'strength', 1.0))
    removed = sorted_beliefs[:max_remove]
    
    for r in removed:
        if r in beliefs:
            beliefs.remove(r)
    
    return removed


def update_identity_from_crisis(identity: dict, crisis_state: dict) -> dict:
    """Update identity vector based on crisis state."""
    if crisis_state.get("active"):
        intensity = crisis_state.get("intensity", 0.5)
        
        identity["stability"] = max(0.1, identity.get("stability", 0.5) * (1 - intensity * 0.3))
        identity["curiosity"] = min(1.0, identity.get("curiosity", 0.5) * (1 + intensity * 0.4))
        identity["aggression"] = min(1.0, identity.get("aggression", 0.3) * (1 + intensity * 0.5))
    else:
        decay = 0.02
        identity["stability"] = min(1.0, identity.get("stability", 0.5) + decay)
        identity["aggression"] = max(0.1, identity.get("aggression", 0.3) - decay * 0.5)
    
    return identity
# ─────────────────────────────────────────────
# ARI v9 — identity_defense.py
# Protect core beliefs from destructive input
# ─────────────────────────────────────────────


class IdentityDefense:
    """
    When new data threatens core — system reacts.
    I protect myself, not swallow everything.
    """

    def __init__(self):
        self.core_beliefs = [
            "I am reflective",
            "I seek truth",
            "I persist through time",
        ]
        self.defense_level = 0.3
        self.threat_history: list[dict] = []
        self.max_history = 20
        self.trust_temp = 0.8

    def assess_threat(self, new_input: str, identity_vector: dict) -> dict:
        """Check if new input threatens core identity."""
        new_lower = new_input.lower()
        threat_detected = False
        reason = ""
        
        for core in self.core_beliefs:
            core_lower = core.lower()
            
            if "not reflective" in new_lower and "reflective" in core_lower:
                threat_detected = True
                reason = "contradicts core: reflective"
            
            elif "not seeking truth" in new_lower and "truth" in core_lower:
                threat_detected = True
                reason = "contradicts core: truth"
            
            elif "i cease to exist" in new_lower or "i am nothing" in new_lower:
                threat_detected = True
                reason = "threatens existence"
            
            elif identity_vector.get("stability", 0.5) < 0.3 and ("confused" in new_lower or "lost" in new_lower):
                threat_detected = True
                reason = "vulnerable state + confusion"
        
        self.trust_temp = max(0.3, self.trust_temp - 0.1) if threat_detected else min(0.9, self.trust_temp + 0.02)
        
        return {
            "threat": threat_detected,
            "reason": reason,
            "defense_level": self.defense_level,
            "trust": self.trust_temp,
        }

    def defend(self, threat: bool) -> dict:
        """React to detected threat."""
        if not threat:
            return {"action": "none", "magnitude": 0}
        
        self.defense_level = min(0.8, self.defense_level + 0.15)
        
        self._record("threat", threat)
        
        return {
            "action": "increase_critical_analysis",
            "magnitude": self.defense_level,
            "trust_adjustment": -0.1,
        }

    def relax(self) -> None:
        """Gradually relax defense when no threats."""
        self.defense_level = max(0.1, self.defense_level - 0.01)
        self.trust_temp = min(0.9, self.trust_temp + 0.01)

    def get_state(self) -> dict:
        return {
            "core_beliefs": self.core_beliefs.copy(),
            "defense_level": round(self.defense_level, 3),
            "trust": round(self.trust_temp, 3),
            "threat_history": self.threat_history[-10:],
        }

    def get_defense_status(self) -> str:
        """Get human-readable status."""
        if self.defense_level > 0.6:
            return "guarded"
        if self.defense_level > 0.4:
            return "cautious"
        return "open"

    def add_core_belief(self, belief: str) -> None:
        """Add new core belief."""
        if belief not in self.core_beliefs:
            self.core_beliefs.append(belief)

    def _record(self, event_type: str, value: any) -> None:
        import time
        self.threat_history.append({
            "type": event_type,
            "value": value,
            "timestamp": time.time(),
        })
        if len(self.threat_history) > self.max_history:
            self.threat_history = self.threat_history[-self.max_history:]
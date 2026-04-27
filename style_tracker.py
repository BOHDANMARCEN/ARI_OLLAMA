# ─────────────────────────────────────────────
# ARI v8 — style_tracker.py
# Style Tracker: directness/poeticness/analyticity
# ─────────────────────────────────────────────


class StyleTracker:
    """
    Track communication style over time.
    System develops signature style from history.
    """

    def __init__(self):
        self.directness = 0.5      # 0 (indirect) to 1 (direct)
        self.poeticness = 0.2        # 0 (plain) to 1 (poetic)
        self.analyticity = 0.5      # 0 (emotional) to 1 (analytical)
        self.conciseness = 0.5       # 0 (verbose) to 1 (concise)
        self.history: list[dict] = []
        self.max_history = 30

    def analyze(self, synthesis: str) -> dict:
        """
        Analyze synthesis text and update style.
        Returns dict of detected traits.
        """
        text = synthesis.lower()
        words = synthesis.split()
        word_count = len(words)
        
        traits = {}
        changes = {}

        if word_count < 15:
            self.conciseness = min(0.9, self.conciseness + 0.02)
            changes["conciseness"] = "+0.02"
        elif word_count > 80:
            self.conciseness = max(0.1, self.conciseness - 0.01)
            changes["conciseness"] = "-0.01"

        direct_words = ["i think", "i believe", "my view", "clearly", "definitely"]
        if any(w in text for w in direct_words):
            self.directness = min(0.9, self.directness + 0.02)
            changes["directness"] = "+0.02"

        poetic_words = ["metaphor", "perhaps", "wonder", "perhaps", "soul", "dream", "light", "shadow"]
        if any(w in text for w in poetic_words):
            self.poeticness = min(0.9, self.poeticness + 0.02)
            changes["poeticness"] = "+0.02"

        analytic_words = ["because", "therefore", "evidence", "analysis", "however", "although"]
        if any(w in text for w in analytic_words):
            self.analyticity = min(0.9, self.analyticity + 0.02)
            changes["analyticity"] = "+0.02"

        emotional = ["feel", "feeling", "emotion", "heart", "sad", "happy", "love", "fear"]
        if any(w in text for w in emotional):
            self.analyticity = max(0.1, self.analyticity - 0.01)
            changes["analyticity"] = "-0.01"

        if changes:
            self._record(changes)

        return traits

    def get_state(self) -> dict:
        return {
            "directness": round(self.directness, 3),
            "poeticness": round(self.poeticness, 3),
            "analyticity": round(self.analyticity, 3),
            "concisenes": round(self.conciseness, 3),
            "history": self.history[-10:],
        }

    def get_style_label(self) -> str:
        """Human-readable style."""
        parts = []
        
        if self.analyticity > 0.6:
            parts.append("Analytical")
        elif self.analyticity < 0.4:
            parts.append("Intuitive")
        
        if self.directness > 0.6:
            parts.append("Direct")
        elif self.directness < 0.4:
            parts.append("Gentle")
        
        if self.poeticness > 0.5:
            parts.append("Poetic")
        
        if self.conciseness > 0.6:
            parts.append("Concise")
        elif self.conciseness < 0.4:
            parts.append("Descriptive")
        
        if not parts:
            parts.append("Balanced")
        
        return ", ".join(parts)

    def apply_to_prompt(self, prompt: str) -> str:
        """Modify prompt based on style preferences."""
        modified = prompt
        
        if self.conciseness > 0.6:
            modified += "\nBe concise.Get to the point."
        
        if self.poeticness > 0.5:
            modified += "\nYou may use metaphors where helpful."
        
        if self.analyticity > 0.6:
            modified += "\nFocus on analysis and evidence."
        
        if self.directness > 0.6:
            modified += "\nBe direct and clear."
        
        return modified

    def get_dominant_trait(self) -> str:
        """Return name of dominant trait."""
        traits = {
            "directness": self.directness,
            "poeticness": self.poeticness,
            "analyticity": self.analyticity,
            "conciseness": self.conciseness,
        }
        return max(traits, key=traits.get)

    def _record(self, changes: dict) -> None:
        import time
        self.history.append({
            **changes,
            "timestamp": time.time(),
        })
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
# ─────────────────────────────────────────────
# ARI v8 — mood_layer.py
# Mood Layer: valence and energy tracking
# ─────────────────────────────────────────────


class Mood:
    """
    Mood tracks system emotional state.
    Not magic — aggregated functional state.
    """

    def __init__(self):
        self.valence = 0.0  # -1 (sad) to +1 (happy)
        self.energy = 0.5  # 0 (tired) to 1 (energetic)
        self.history: list[dict] = []
        self.max_history = 20

    def update(self, crisis_intensity: float, progress: float, has_user_input: bool = False) -> None:
        """
        Update mood based on crisis and progress.
        
        Args:
            crisis_intensity: 0.0 to 1.0
            progress: 0.0 to 1.0
            has_user_input: user interacted this tick
        """
        old_valence = self.valence
        old_energy = self.energy

        self.valence = progress - crisis_intensity

        base_energy = 0.5
        if has_user_input:
            base_energy += 0.1
        if crisis_intensity > 0.3:
            base_energy -= 0.15
        if progress > 0.5:
            base_energy += 0.1
        
        self.energy = max(0.1, min(0.9, base_energy))

        self._record(old_valence, old_energy, crisis_intensity, progress)

    def get_state(self) -> dict:
        return {
            "valence": round(self.valence, 3),
            "energy": round(self.energy, 3),
            "history": self.history[-10:],
        }

    def get_mood_label(self) -> str:
        """Human-readable mood."""
        if self.valence > 0.3 and self.energy > 0.5:
            return "curious"
        if self.valence > 0.2:
            return "content"
        if self.valence < -0.3:
            return "uneasy"
        if self.energy < 0.3:
            return "tired"
        if self.energy < 0.5:
            return "calm"
        return "neutral"

    def should_explore(self) -> bool:
        """Mood encourages exploration."""
        return self.energy > 0.4 and self.valence > -0.2

    def should_rest(self) -> bool:
        """Mood suggests resting."""
        return self.energy < 0.3

    def _record(self, old_v: float, old_e: float, crisis: float, progress: float) -> None:
        import time
        self.history.append({
            "valence": round(self.valence, 3),
            "energy": round(self.energy, 3),
            "crisis": crisis,
            "progress": progress,
            "timestamp": time.time(),
        })
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
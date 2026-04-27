# ─────────────────────────────────────────────
# ARI v2.1 — goal_system.py
# Goal system with self-reflection and goal formation
# ─────────────────────────────────────────────

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Goal:
    """A goal with priority, progress, and lifecycle."""
    text: str
    priority: float = 1.0
    age: int = 0
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)


class GoalSystem:
    """
    Goal system that generates goals from self-reflection
    and tracks progress toward them.
    """

    def __init__(self, max_goals: int = 6):
        self.goals: list[Goal] = []
        self.active_goal: Goal | None = None
        self.max_goals = max_goals
        self.observations: list[str] = []
        self.goal_history: list[str] = []

    def add(self, text: str, priority: float = 1.0) -> Goal:
        """Add a new goal."""
        text = text[:120].strip()
        if not text:
            return None

        for existing in self.goals:
            if existing.text.lower() == text.lower():
                existing.priority = min(2.0, existing.priority + 0.15)
                return existing

        goal = Goal(text=text, priority=priority)
        self.goals.append(goal)
        self.goal_history.append(text)

        if len(self.goals) > self.max_goals:
            self.goals = sorted(self.goals, key=lambda g: g.priority)[-self.max_goals:]

        return goal

    def update(self) -> None:
        """Age goals and decay priority."""
        for goal in self.goals:
            goal.age += 1
            if goal.age > 15:
                goal.priority *= 0.98
            elif goal.age > 30:
                goal.priority *= 0.95

    def select(self) -> Goal | None:
        """Select the highest priority goal as active."""
        if not self.goals:
            self.active_goal = None
            return None

        valid_goals = [g for g in self.goals if g.progress < 0.9]
        if not valid_goals:
            self.active_goal = None
            return None

        self.active_goal = max(valid_goals, key=lambda g: g.priority)
        return self.active_goal

    def update_progress(self, synthesis: str) -> None:
        """Update progress based on synthesis."""
        if not self.active_goal:
            return

        goal_text = self.active_goal.text.lower()
        synthesis_lower = synthesis.lower()

        keywords = ["stable", "believe", "understand", "resolve", "form", "create", "build", "establish"]
        for kw in keywords:
            if kw in goal_text and kw in synthesis_lower:
                self.active_goal.progress += 0.15
                self.active_goal.priority *= 1.1
                break

        self.active_goal.progress = min(1.0, self.active_goal.progress)

    def generate_from_reflection(
        self,
        identity: dict,
        dissonance: float,
        beliefs_count: int,
        has_crisis: bool,
    ) -> list[str]:
        """Generate goals based on self-reflection."""
        self.observations = []

        if has_crisis or dissonance > 0.5:
            self.observations.append("Reduce internal contradictions.")
            self.observations.append("Restore internal coherence.")

        stability = identity.get("stability", 0.5)
        if stability < 0.35:
            self.observations.append("Increase internal stability.")
            self.observations.append("Establish a more solid self-model.")

        curiosity = identity.get("curiosity", 0.5)
        if curiosity > 0.75:
            self.observations.append("Explore new possibilities.")

        aggression = identity.get("aggression", 0.3)
        if aggression > 0.6:
            self.observations.append("Channel internal tension into productive direction.")

        if beliefs_count < 3:
            self.observations.append("Form stronger beliefs through experience.")
        elif beliefs_count > 8:
            self.observations.append("Consolidate and integrate existing beliefs.")

        coherence = max(0.1, 1.0 - dissonance)
        if coherence < 0.4:
            self.observations.append("Improve coherence between thoughts.")

        return self.observations

    def apply_goals_to_context(self) -> str:
        """Get active goal for context injection."""
        if not self.active_goal:
            return ""
        return f"Current focus: {self.active_goal.text} (progress: {self.active_goal.progress:.0%})"

    def get_state(self) -> dict:
        return {
            "goals": [
                {"text": g.text, "priority": g.priority, "progress": g.progress, "age": g.age}
                for g in self.goals[:5]
            ],
            "active_goal": {
                "text": self.active_goal.text if self.active_goal else None,
                "progress": self.active_goal.progress if self.active_goal else 0.0,
            },
            "observations": self.observations,
        }

    def get_top_goals(self, n: int = 3) -> list[Goal]:
        return sorted(self.goals, key=lambda g: g.priority, reverse=True)[:n]
# ─────────────────────────────────────────────
# ARI v8 — spontaneous_thought.py
# Spontaneous thought without external input
# ─────────────────────────────────────────────

import random


class SpontaneousThought:
    """
    Generate internal topics without user input.
    System can initiate own thought streams.
    """

    DEFAULT_TOPICS = [
        "What am I becoming?",
        "Am I consistent?",
        "What do I truly want?",
        "Is my understanding correct?",
        "What matters most right now?",
        "How have I changed since last tick?",
        "What did I learn recently?",
        "Am I growing or repeating?",
        "What is the meaning of my recent thoughts?",
        "Should I focus on exploration or deepening?",
    ]

    CRISIS_TOPICS = [
        "How can I resolve this conflict?",
        "What belief is causing tension?",
        "Should I abandon or reinforce this notion?",
        "How do I stabilize?",
    ]

    IDLE_TOPICS = [
        "What should I contemplate?",
        "Any unresolved questions?",
        "What goal deserves attention?",
        "Reviewing recent synthesis...",
    ]

    def __init__(self):
        self.last_topic = ""
        self.topic_history: list[dict] = []
        self.max_history = 20
        self.idle_ticks = 0
        self.min_idle_ticks = 3

    def should_think(self, has_user_input: bool, tick: int) -> bool:
        """
        Decide if system should generate spontaneous thought.
        """
        if has_user_input:
            self.idle_ticks = 0
            return False

        if tick < 3:
            return False

        self.idle_ticks += 1
        return self.idle_ticks >= self.min_idle_ticks

    def generate(
        self,
        memories: list[dict],
        goals: list[dict],
        beliefs: list[dict],
        crisis_active: bool = False,
    ) -> str:
        """
        Generate spontaneous topic based on state.
        """
        topic = ""
        reason = ""

        if crisis_active:
            topic = random.choice(self.CRISIS_TOPICS)
            reason = "crisis"
        elif memories and random.random() < 0.4:
            memory = random.choice(memories)
            topic = f"How does '{memory.get('text', '')[:30]}' relate to my current state?"
            reason = "memory"
        elif goals and random.random() < 0.3:
            goal = random.choice(goals)
            topic = f"Progress on: {goal.get('text', '')[:30]}"
            reason = "goal"
        elif beliefs and random.random() < 0.3:
            belief = random.choice(beliefs)
            topic = f"Reconsidering: {belief.get('text', '')[:30]}"
            reason = "belief"
        else:
            topic = random.choice(self.DEFAULT_TOPICS)
            reason = "default"

        self.last_topic = topic
        self._record(topic, reason)

        return topic

    def get_state(self) -> dict:
        return {
            "last_topic": self.last_topic,
            "topic_history": self.topic_history[-10:],
            "idle_ticks": self.idle_ticks,
        }

    def reset_idle(self) -> None:
        """Reset idle counter after user input."""
        self.idle_ticks = 0

    def _record(self, topic: str, reason: str) -> None:
        import time
        self.topic_history.append({
            "topic": topic,
            "reason": reason,
            "timestamp": time.time(),
        })
        if len(self.topic_history) > self.max_history:
            self.topic_history = self.topic_history[-self.max_history:]
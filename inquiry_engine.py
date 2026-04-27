# ─────────────────────────────────────────────
# ARI v2.1 — inquiry_engine.py
# Self-Inquiry Engine: generates internal questions
# ─────────────────────────────────────────────

import random
from typing import Any


class InquiryEngine:
    """
    Self-Inquiry Engine generates questions for the system to ask itself.
    Runs every 5 ticks + immediately on crisis.
    """

    CRISIS_QUESTIONS = [
        "What beliefs are causing the current conflict?",
        "Why am I experiencing internal tension?",
        "What should I prioritize to restore balance?",
        "Which belief is most unstable right now?",
    ]

    STABILITY_QUESTIONS = [
        "Why is my stability low?",
        "What external factors affect my stability?",
        "How can I become more grounded?",
        "What gives me a sense of firm ground?",
    ]

    GOAL_QUESTIONS = [
        "Why am I failing my current goal?",
        "Is my goal still relevant?",
        "What obstacles block my progress?",
        "Should I revise my approach?",
    ]

    GENERAL_QUESTIONS = [
        "What should I improve next?",
        "What patterns am I noticing in myself?",
        "How am I evolving between ticks?",
        "What is the most important thing right now?",
        "What am I learning about myself?",
        "What beliefs feel most solid?",
        "What thoughts keep returning?",
    ]

    def __init__(self, inquiry_interval: int = 5):
        self.inquiry_interval = inquiry_interval
        self.last_question: str | None = None
        self.question_cooldown = 0

    def should_inquire(self, tick: int, crisis_active: bool) -> bool:
        """Check if we should generate a question."""
        if crisis_active and self.question_cooldown == 0:
            return True
        if tick % self.inquiry_interval == 0 and self.question_cooldown == 0:
            return True
        return False

    def generate_question(
        self,
        tick: int,
        crisis_active: bool,
        identity: dict[str, float],
        goals: list[dict[str, Any]],
    ) -> str | None:
        """Generate appropriate self-question based on state."""
        self.question_cooldown = max(0, self.question_cooldown - 1)

        if crisis_active and self.question_cooldown == 0:
            question = random.choice(self.CRISIS_QUESTIONS)
            self.question_cooldown = 1
            self.last_question = question
            return question

        stability = identity.get("stability", 0.5)
        if stability < 0.4 and self.question_cooldown == 0:
            question = random.choice(self.STABILITY_QUESTIONS)
            self.question_cooldown = 1
            self.last_question = question
            return question

        if goals:
            active_goal = None
            for g in goals:
                if isinstance(g, dict):
                    prog = g.get("progress", 0.0)
                    if prog < 0.3:
                        active_goal = g
                        break
            
            if active_goal and self.question_cooldown == 0:
                question = random.choice(self.GOAL_QUESTIONS)
                self.question_cooldown = 1
                self.last_question = question
                return question

        if tick % self.inquiry_interval == 0 and self.question_cooldown == 0:
            question = random.choice(self.GENERAL_QUESTIONS)
            self.question_cooldown = 1
            self.last_question = question
            return question

        return None

    def get_question_for_llm(self) -> str:
        """Format question for LLM pass."""
        if not self.last_question:
            return "What should I reflect on?"
        return self.last_question

    def get_state(self) -> dict:
        return {
            "last_question": self.last_question,
            "question_cooldown": self.question_cooldown,
            "inquiry_interval": self.inquiry_interval,
        }
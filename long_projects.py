# ─────────────────────────────────────────────
# ARI v9 — long_projects.py
# Multi-cycle goals
# ─────────────────────────────────────────────


class LongProject:
    """A goal spanning many cycles."""

    def __init__(self, name: str, horizon: int = 50):
        self.name = name
        self.progress = 0.0
        self.horizon = horizon
        self.created_at = None
        self.updated_at = None

    def update(self, delta: float = 0.01) -> None:
        import time
        self.progress = min(1.0, self.progress + delta)
        self.updated_at = time.time()
        if not self.created_at:
            self.created_at = time.time()

    def percent_complete(self) -> float:
        return self.progress * 100

    def is_complete(self) -> bool:
        return self.progress >= 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "progress": self.progress,
            "horizon": self.horizon,
            "percent": self.percent_complete(),
        }


class LongProjects:
    """
    Goals on many cycles.
    """

    def __init__(self):
        self.projects: list[LongProject] = []
        self.max_projects = 5

    def add(self, name: str, horizon: int = 50) -> None:
        """Add new long project."""
        if len(self.projects) >= self.max_projects:
            self.projects = self.projects[1:]
        
        self.projects.append(LongProject(name, horizon))

    def update_all(self, synthesis: str) -> None:
        """Update progress based on synthesis."""
        text = synthesis.lower()
        
        for project in self.projects:
            if project.is_complete():
                continue
            
            if project.name.lower() in text:
                project.update(0.03)
            
            elif "progress" in text or "learned" in text:
                project.update(0.01)

    def get_active(self) -> list[dict]:
        """Get active projects."""
        return [p.to_dict() for p in self.projects if not p.is_complete()]

    def get_completed(self) -> list[dict]:
        """Get completed projects."""
        return [p.to_dict() for p in self.projects if p.is_complete()]

    def get_state(self) -> dict:
        return {
            "active": self.get_active(),
            "completed": self.get_completed(),
            "total": len(self.projects),
        }

    def get_summary(self) -> str:
        """Get summary text."""
        active = self.get_active()
        
        if not active:
            return "No active long projects."
        
        if len(active) == 1:
            p = active[0]
            return f"{p['name']}: {p['percent']:.0f}%"
        
        return f"{len(active)} active projects"

    def bias_towards_horizon(self) -> str:
        """Get bias text towards long-term thinking."""
        active = self.get_active()
        
        if not active:
            return ""
        
        longest = max(active, key=lambda x: x["horizon"])
        return f"Thinking about: {longest['name']} ({longest['percent']:.0f}%)"
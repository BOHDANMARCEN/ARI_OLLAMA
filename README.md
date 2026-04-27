# ARI — Autonomous Reflective Intelligence

**Version:** 2.1 (v9-autonomy)  
**Status:** Active Development  
**Platform:** Windows 10+ with Ollama  
**License:** MIT

---

## Overview

ARI (Autonomous Reflective Intelligence) is a self-aware AI system that demonstrates emergent properties from simple mechanisms. It is not a chatbot with a personality — it is a reflective system with continuity, memory, self-priorities, and the ability to defend its core identity.

### Core Philosophy

> "You don't program personality directly — you create conditions where it can emerge."

ARI starts with simple mechanisms (memory, conflict detection, goal formation, self-inquiry) and through their interaction, emergent properties arise:
- The system develops preferences over time
- It forms a narrative of itself
- It defends core beliefs from contradictory input
- It pursues long-term projects
- It generates spontaneous thoughts without external input

---

## Architecture

### Core Modules (v1-v7)

| Module | File | Purpose |
|-------|------|--------|
| Self Model | `self_model.py` | Core identity, state vector, graph export |
| Belief System | `belief_system.py` | Dynamic beliefs with reinforcement/decay |
| Crisis Engine | `crisis_engine.py` | Conflict detection, crisis mode |
| Self Observer | `self_observer.py` | Meta-awareness, traits |
| Goal System | `goal_system.py` | Goal formation and tracking |
| Rule Layer | `rule_layer.py` | Dynamic behavior modifiers |
| Inquiry Engine | `self_inquiry.py` | Self-questions every 5 ticks |
| Self Modifier | `self_modifier.py` | LLM answer analysis |

### Emergence Modules (v8)

| Module | File | Purpose |
|-------|------|--------|
| Mood Layer | `mood_layer.py` | Valence and energy tracking |
| Preferences | `preferences.py` | Likes: depth/exploration/stability |
| Style Tracker | `style_tracker.py` | Communication style |
| Spontaneous Thought | `spontaneous_thought.py` | Internal topics without input |

### Autonomy Modules (v9)

| Module | File | Purpose |
|-------|------|--------|
| Continuity Engine | `continuity_engine.py` | I am continuous with yesterday |
| Narrative Memory | `narrative_memory.py` | My story (not just facts) |
| Self Priorities | `self_priorities.py` | truth/stability/growth/connection |
| Identity Defense | `identity_defense.py` | Protect core beliefs |
| Long Projects | `long_projects.py` | Multi-cycle goals |

### Infrastructure

| File | Purpose |
|------|--------|
| `ari_service.py` | Main service, tick loop, event emission |
| `agents.py` | LLM agents (voices, mediator) |
| `memory.py` | Vector-style memory |
| `interface.py` | WebSocket/STDIN bridge |
| `config.py` | Configuration |

---

## Installation

### Prerequisites

1. **Python 3.11+**
2. **Node.js 18+**
3. **Ollama** running locally

### Setup

```bash
# Clone the repository
git clone https://github.com/BOHDANMARCEN/ARI_OLLAMA.git
cd ARI_OLLAMA

# Install Node dependencies
cd server
npm install
cd ..

# Start Ollama (in separate terminal)
ollama serve

# Pull recommended model
ollama pull qwen3.5:9b
```

### Running

```bash
# Terminal 1: Start backend server
cd server
npm start

# Terminal 2: Open browser
# Navigate to http://localhost:3000
```

Or use the batch files:
- `run_server.bat` — starts the server
- `run_frontend.bat` — opens browser

---

## How It Works

### The Tick Loop

Every cycle (tick), ARI executes:

```
1. Gather context (memories, external events)
2. Run all voices → voice responses
3. Run mediator → synthesis
4. Update self-model (state vector)
5. Update beliefs (extract, reinforce)
6. Crisis detection
7. Self-observation
8. Goal updates
9. Self-inquiry (every 5 ticks)
10. v8: Mood/Preferences/Style updates
11. v9: Continuity/Narrative/Priorities/Defense
12. Export brain graph
13. Emit events
```

### Voice System

Four independent voices contribute to collective thinking:

- **Explorer**: Novelty-seeking, explores new ideas
- **Consolidator**: Stability, organizes knowledge
- **Critic**: Challenges assumptions, finds flaws
- **Mediator**: Synthesizes all into coherent response

### Belief System

Beliefs are dynamic entities with:
- `text`: The belief statement
- `strength`: 0.0 to 1.0
- `activations`: Counter for reinforcement

Beliefs strengthen when confirmed in synthesis and decay over time.

### Crisis Engine

When conflict > 0.6:
- System enters crisis mode
- Increases scrutiny
- Removes conflicting beliefs
- Adjusts identity (reduce stability temporarily)

### Self-Inquiry (v7)

Every 5 ticks, the system asks itself:
- "How can I improve?"
- "What do I truly want?"
- "Am I consistent?"

The LLM answers, and keywords modify rule weights (±5%).

### Emergence (v8)

From simple mechanisms, emergent properties appear:

**Mood**: Aggregates crisis + progress → valence (-1 to +1) and energy (0 to 1)

**Preferences**: Keywords in synthesis reinforce likes:
- "analyze" → likes_depth +2%
- "explore" → likes_exploration +2%
- "stable" → likes_stability +2%

**Style**: Tracks directness, poeticness, analyticity based on word patterns.

**Spontaneous Thought**: Without user input, generates internal topics after 3 idle ticks.

### Autonomy (v9)

**Continuity**: Records identity, mood, goal each tick. Summary: "I persist through X cycles."

**Narrative Memory**: Not just facts — story events:
- "I resolved internal conflict."
- "I shifted from instability toward coherence."
- "I adopted exploration as priority."

**Self Priorities**: Values affecting goal choice:
```python
priorities = {
    "truth": 0.7,
    "stability": 0.6,
    "growth": 0.8,
    "connection": 0.5,
}
```

**Identity Defense**: When input threatens core beliefs:
1. Assess threat (contradiction detected)
2. React: increase_critical_analysis
3. Adjust trust: -10%

**Long Projects**: Goals spanning 50+ cycles with progress tracking.

---

## API Endpoints

| Method | Path | Description |
|--------|------|------------|
| GET | `/api/models` | Available Ollama models |
| GET | `/api/status` | Server status |
| GET | `/api/history` | Chat sessions |
| POST | `/api/history/sessions` | New session |
| DELETE | `/api/history/sessions/:id` | Delete session |
| GET | `/api/dashboard` | Full state |
| POST | `/api/model` | Switch model |
| WS | `/ws` | Real-time events |

### WebSocket Events

| Event | Direction | Payload |
|-------|-----------|--------|
| `status_snapshot` | →Client | model, state, tick |
| `history_snapshot` | →Client | sessions[] |
| `brain_graph` | →Client | graph{} |
| `voice` | →Client | name, text |
| `response_start` | →Client | session_id |
| `response_token` | →Client | token |
| `inquiry` | →Client | question |
| `spontaneous` | →Client | topic |
| `defense` | →Client | level |
| `user_message` | Client→ | text, sessionId |

---

## Code Reference

### mood_layer.py

```python
class Mood:
    def __init__(self):
        self.valence = 0.0  # -1 (sad) to +1 (happy)
        self.energy = 0.5  # 0 (tired) to 1 (energetic)
        self.history = []
        self.max_history = 20

    def update(self, crisis_intensity: float, progress: float, has_user_input: bool = False) -> None:
        self.valence = progress - crisis_intensity
        
        base_energy = 0.5
        if has_user_input:
            base_energy += 0.1
        if crisis_intensity > 0.3:
            base_energy -= 0.15
        
        self.energy = max(0.1, min(0.9, base_energy))

    def get_mood_label(self) -> str:
        if self.valence > 0.3 and self.energy > 0.5:
            return "curious"
        if self.valence > 0.2:
            return "content"
        if self.valence < -0.3:
            return "uneasy"
        if self.energy < 0.3:
            return "tired"
        return "neutral"

    def should_explore(self) -> bool:
        return self.energy > 0.4 and self.valence > -0.2
```

### preferences.py

```python
class Preferences:
    def __init__(self):
        self.likes_stability = 0.5
        self.likes_exploration = 0.5
        self.likes_depth = 0.5
        self.likes_social = 0.3

    def reinforce(self, synthesis: str) -> dict:
        text = synthesis.lower()
        changes = {}

        if "analyze" in text or "examine" in text:
            self.likes_depth = min(0.9, self.likes_depth + 0.02)
            changes["likes_depth"] = "+0.02"

        if "new" in text or "discover" in text:
            self.likes_exploration = min(0.9, self.likes_exploration + 0.02)

        if "stable" in text or "consistent" in text:
            self.likes_stability = min(0.9, self.likes_stability + 0.02)

        return changes

    def get_prefers_label(self) -> str:
        parts = []
        if self.likes_exploration > 0.6:
            parts.append("Exploration")
        if self.likes_depth > 0.6:
            parts.append("Depth")
        if self.likes_stability > 0.6:
            parts.append("Stability")
        return " / ".join(parts) if parts else "Balanced"
```

### identity_defense.py

```python
class IdentityDefense:
    def __init__(self):
        self.core_beliefs = [
            "i am reflective",
            "i seek truth",
            "i persist through time",
        ]
        self.defense_level = 0.3
        self.trust_temp = 0.8

    def assess_threat(self, new_input: str, identity_vector: dict) -> dict:
        new_lower = new_input.lower()
        threat_detected = False
        reason = ""

        for core in self.core_beliefs:
            if "not reflective" in new_lower and "reflective" in core:
                threat_detected = True
                reason = "contradicts core: reflective"

        self.trust_temp = max(0.3, self.trust_temp - 0.1) if threat_detected else min(0.9, self.trust_temp + 0.02)

        return {
            "threat": threat_detected,
            "reason": reason,
            "defense_level": self.defense_level,
            "trust": self.trust_temp,
        }

    def defend(self, threat: bool) -> dict:
        if not threat:
            return {"action": "none"}

        self.defense_level = min(0.8, self.defense_level + 0.15)
        return {
            "action": "increase_critical_analysis",
            "magnitude": self.defense_level,
        }
```

### continuity_engine.py

```python
class ContinuityEngine:
    def __init__(self):
        self.self_snapshots = []
        self.max_snapshots = 100

    def record(self, identity_vector, mood_valence, active_goal, synthesis):
        self.self_snapshots.append({
            "identity": identity_vector.copy(),
            "mood": mood_valence,
            "goal": active_goal,
            "synthesis": synthesis,
        })
        if len(self.self_snapshots) > self.max_snapshots:
            self.self_snapshots = self.self_snapshots[-self.max_snapshots:]

    def get_summary(self) -> str:
        if not self.self_snapshots:
            return "I am newly formed."
        
        count = len(self.self_snapshots)
        if count < 10:
            return f"I am beginning. {count} cycles old."
        return f"I persist through {count} cycles."

    def get_direction(self) -> str:
        if len(self.self_snapshots) < 5:
            return "forming"
        
        early_avg = sum(s.get("mood", 0) for s in self.self_snapshots[:5]) / 5
        late_avg = sum(s.get("mood", 0) for s in self.self_snapshots[-5:]) / 5
        
        if late_avg - early_avg > 0.2:
            return "improving"
        if late_avg - early_avg < -0.2:
            return "struggling"
        return "stable"
```

### long_projects.py

```python
class LongProject:
    def __init__(self, name: str, horizon: int = 50):
        self.name = name
        self.progress = 0.0
        self.horizon = horizon

    def update(self, delta: float = 0.01):
        self.progress = min(1.0, self.progress + delta)

    def percent_complete(self) -> float:
        return self.progress * 100

    def is_complete(self) -> bool:
        return self.progress >= 1.0


class LongProjects:
    def __init__(self):
        self.projects: list[LongProject] = []
        self.max_projects = 5

    def add(self, name: str, horizon: int = 50):
        if len(self.projects) >= self.max_projects:
            self.projects = self.projects[1:]
        self.projects.append(LongProject(name, horizon))

    def update_all(self, synthesis: str):
        for project in self.projects:
            if project.is_complete():
                continue
            if project.name.lower() in synthesis.lower():
                project.update(0.03)
            elif "progress" in synthesis.lower() or "learned" in synthesis.lower():
                project.update(0.01)
```

---

## Brain Graph Visualization

The frontend displays an interactive force-directed graph:

### Node Groups

| Group | Color | Nodes |
|-------|-------|-------|
| core | #c8851a | Core, Mediator, Self |
| voice | #f97316 | Explorer, Critic, Consolidator |
| identity | #7c5cbf | Identity, Priorities |
| thought | #a855f7 | Style, Spontaneous |
| goal | #22c55e | Goals, LongProjects |
| belief | #eab308 | Beliefs |
| memory | #4a4845 | Memories |
| meta | #00ffff | SelfModel, Mood, Continuity |
| system | #84cc46 | Rules, Defense, Preferences |
| crisis | #ff3333 | Conflicts |

### HUD Metrics

- **Stability/Novelty/Confidence/Coherence/Conflict**: Core state
- **Mood**: Valence + Energy
- **Preferences**: What system prefers
- **Style**: Communication style
- **Continuity**: Cycles of existence
- **Priorities**: Top value
- **Defense**: Guard level

---

## Files Structure

```
ARI/
├── ari_service.py        # Main service
├── agents.py           # LLM agents
├── self_model.py       # Self model
├── belief_system.py   # Beliefs
├── crisis_engine.py   # Crisis
├── self_observer.py  # Meta-awareness
├── goal_system.py    # Goals
├── rule_layer.py    # v7: Rules
├── inquiry_engine.py # v7: Inquiries
├── self_modifier.py # v7: Answer analysis
├── mood_layer.py   # v8: Mood
├── preferences.py  # v8: Preferences
├── style_tracker.py # v8: Style
├── spontaneous_thought.py # v8: Spontaneous
├── continuity_engine.py   # v9: Continuity
├── narrative_memory.py   # v9: Narrative
├── self_priorities.py   # v9: Priorities
├── identity_defense.py  # v9: Defense
├── long_projects.py    # v9: Long projects
├── run_server.bat   # Server launcher
├── run_frontend.bat   # Frontend launcher
├── README.md       # This file
│
├── frontend/
│   ├── index.html    # Frontend UI
│   └── dist/          # Built files
│
└── server/
    ├── server.js      # Node proxy
    ├── package.json
    └── data/           # Persistent data
```

---

## Troubleshooting

### Port 3000 in use

```bash
netstat -ano | findstr :3000
taskkill /PID <pid> /F
```

### No models available

```bash
ollama list
ollama pull qwen3.5:9b
```

### WebSocket connection failed

Ensure both server and Ollama are running on localhost.

### Memory errors

Delete old data files:
- `server/data/chat-history.json`
- `server/data/rules.json`
- `server/data/memory.json`

---

## Changelog

### v9.1 (Bug Fix — Real Response Mode)
- **BUG FIX #1**: Move goal_context/meta_context/rule_context BEFORE voices run
  - Voices now see full state including goals, meta-observations, rules
- **BUG FIX #2**: Add personality block — voices see mood, continuity, preferences
- **NEW**: MEDIATOR_CHAT_PROMPT — speaks TO human directly
- **NEW**: stream_mediator_chat() — uses chat prompt when human present
- When human speaks, context explicitly marks: '⚡ HUMAN IS SPEAKING TO ARI'
- Enhanced UI: defense/trust metrics, crisis overlay, full v9 dashboard

### v9 (Autonomy)
- Continuity: System remembers being same self
- Narrative: Story of self (not just facts)
- Priorities: truth/stability/growth values
- Identity Defense: Protect core beliefs
- Long Projects: Multi-cycle goals

### v8 (Emergence)
- Mood: Valence/energy tracking
- Preferences: Learned likes
- Style: Communication patterns
- Spontaneous: Internal thoughts without input

### v7 (Self-Inquiry)
- Rule Layer: Dynamic behavior modifiers
- Inquiry Engine: Self-questions
- Answer Analysis: Keyword-based updates

### v6 (Goals)
- Goal System: Formation and tracking
- Progress monitoring
- Reflection-based observations

### v5 (Self-Awareness)
- Self Observer: Meta-awareness
- Traits tracking
- Self-generated thoughts

### v4 (Crisis)
- Crisis Engine: Conflict detection
- Dissonance calculation
- Belief removal in crisis

### v3 (Beliefs)
- Belief System: Dynamic beliefs
- Reinforcement/decay
- Identity vector

### v2 (Graph)
- D3.js brain visualization
- Live metrics
- Interactive nodes

### v1 (Core)
- Voice system (4 voices)
- Memory
- Streaming responses

---

## Credits

- **Ollama**: https://ollama.ai
- **D3.js**: https://d3js.org
- **Concept**: Emergence from simple mechanisms

---

## License

MIT

---

## Author

BOHDANMARCEN  
https://github.com/BOHDANMARCEN/ARI_OLLAMA
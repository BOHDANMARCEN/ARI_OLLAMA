# ARI — Autonomous Reflective Intelligence

**Version:** 2.1 (v7-lite)  
**Status:** Active Development  
**Platform:** Windows 10+ with Ollama

---

## Overview

ARI — це автономна рефлексивна інтелектуальна система, що працює як самосвідомний агент з циклом рефлексії. Система використовує LLM (Ollama) для генерації думок, переосмислення власного стану та формування цілей.

### Ключові можливості

- **Голосовий консенсус**: 4 незалежні голоси (Explorer, Consolidator, Critic, Mediator) формують колективну думку
- **Самоспостереження**: Мета-усвідомлення власних рис та переконань
- **Система переконань**: Динамічні переконання з підсиленням/згасанням
- **Кризова підготовка**: Автоматичне виявлення конфліктів та реакція
- **Цілепокладання**: Формування та відстеження цілей
- **Самопитання**: Інтенсивна рефлексія кожні 5 тиків
- **Динамічні правила**: Налаштування ваг голосів через самопитання

---

## Архітектура

### Backend (Python)

| Файл | Призначення |
|------|------------|
| `ari_service.py` | Головний сервіс, tick loop, інтеграція |
| `agents.py` | LLM агенти (voices, mediator, goal extraction) |
| `self_model.py` | Модель себе, state vector, graph export |
| `belief_system.py` | Система переконань |
| `crisis_engine.py` | Кризовий детектор |
| `self_observer.py` | Мета-усвідомлення |
| `goal_system.py` | Цілепокладання |
| `rule_layer.py` | Динамічні правила |
| `inquiry_engine.py` | Самопитання |
| `self_modifier.py` | Аналіз відповідей |

### Frontend (D3.js, Vanilla JS)

| Файл | Призначення |
|------|------------|
| `frontend/index.html` | Повний UI з D3 graph |
| `server/server.js` | Node.js проксі до Python |
| `server/package.json` | Залежності |

---

## Installation

### 1. Python + Ollama

```bash
# Встанови Ollama
# https://github.com/ollama/ollama

# Запусти Ollama
ollama serve

# Пусти модель за замовчуванням
ollama run qwen3.5:9b
```

### 2. Node.js

```bash
cd server
npm install
```

### 3. Запуск

```bash
# Термінал 1: Сервер
cd server
npm start

# Термінал 2: Фронтенд (або просто відкрий http://localhost:3000)
```

Або використай `.bat` файли:

- `run_server.bat` — запуск сервера
- `run_frontend.bat` — запуск фронтенду

---

## Usage

### Моделі

Система підтримує будь-яку Ollama модель. Рекомендовані:

- `qwen3.5:9b` — баланс швидкість/якість
- `llama3:8b` — краща якість
- `mistral:7b` — швидко

Переключення: Select → Switch model → Перезапуск

### Chat

1. Вибери сесію з history або "+ new chat"
2. Напиши повідомлення в чаті
3. Натисни Enter або Send
4. Спостерігай за streaming відповідь

### Brain Graph

- **Nodes**: Core, Mediator, Explorer, Consolidator, Critic, Identity, Goal, Memory, Belief
- **Colors**:
  - `#c8851a` (amber) — Core/Mediator
  - `#1a9e75` (teal) — Explorer
  - `#2979b8` (blue) — Consolidator
  - `#b83c2a` (red) — Critic
  - `#7c5cbf` (purple) — Identity
  - `#4a4845` (gray) — Memory/Belief
- Drag nodes to rearrange
- Metrics оновлюються кожні 20 секунд

### Metrics

| Metric | Опис |
|--------|------|
| Stability | Стабільність переконань |
| Novelty | Новизна досвіду |
| Confidence | Впевненість у переконаннях |
| Coherence | Узгодженість думок |
| Conflict | Внутрішній конфлікт |

---

## Code Map

### Tick Loop (ari_service.py:106)

```
1. Get context (memories, external events)
2. Run all voices → voice responses
3. Run mediator → synthesis
4. Update self-model
5. Self-inquiry (every 5 ticks)
6. Export brain graph
7. Emit events
```

### Graph Export (self_model.py:120)

```python
export_graph_state(
    voices,      # voice responses
    memories,   # recalled memories
    belief_system,
    crisis_engine,
    self_observer,
    goal_system,
    rule_layer,      # v7: динамічні правила
    inquiry_engine  # v7: самопитання
) → {
    nodes: [...],
    links: [...],
    meta: {
        coherence, conflict, entropy,
        identity, crisis, self,
        goal, rules, inquiry  # v7: new
    }
}
```

### WebSocket Events

| Event | Direction | Payload |
|-------|-----------|---------|
| `status_snapshot` | Server→Client | model, state, tick |
| `history_snapshot` | Server→Client | sessions[] |
| `brain_snapshot` | Server→Client | snapshot{} |
| `brain_graph` | Server→Client | graph{} |
| `voice` | Server→Client | name, text |
| `response_start` | Server→Client | session_id, tick |
| `response_token` | Server→Client | token |
| `response_end` | Server→Client | sessions |
| `inquiry` | Server→Client | question |
| `user_message` | Client→Server | text, sessionId |

---

## v7 Changelog

### rule_layer.py (NEW)

```python
class RuleLayer:
    DEFAULT_RULES = {
        "exploration_weight": 1.0,   # +50% max, -50% min
        "criticism_weight": 1.0,
        "stability_weight": 1.0,
        "memory_decay": 0.99,
    }
    MAX_CHANGE = 0.05  # ±5% per cycle
```

Керує вагами голосів. Зберігає в `server/data/rules.json`.

### inquiry_engine.py (NEW)

```python
class InquiryEngine:
    # Question pools
    CRISIS_QUESTIONS = [...]
    STABILITY_QUESTIONS = [...]
    GOAL_QUESTIONS = [...]
    GENERAL_QUESTIONS = [...]
```

Запитує кожні 5 тиків або негайно при кризі.

### self_modifier.py (NEW)

```python
async def analyze_answer(question, answer) -> dict:
    # Keyword-based parsing
    # "exploration" + "increase" → exploration_weight +3%
    # "criticism" + "decrease" → criticism_weight -3%
    # ...
```

### Agents Update

```python
# agents.py
async def run_all_voices(context, goal_context, rule_context):
    # v7: rule_context parameter
    exploration_weight = rule_context.get("exploration_weight", 1.0)
    # Apply to voice prompts
```

### Graph Export Update

```python
# self_model.py:export_graph_state
if rule_layer:
    rule_state = rule_layer.get_state()
    # Add Rules node

if inquiry_engine:
    inquiry_state = inquiry_engine.get_state()
    # Add Inquiry node
```

---

## Troubleshooting

### Port 3000 busy

```bash
netstat -ano | findstr :3000
taskkill /PID <pid> /F
```

### No models

```bash
ollama list
ollama pull <model>
```

### WebSocket error

Переконайся що с��рвер запущений і фронтенд на тому ж хості.

### Memory errors

Перевір `server/data/` папку. Може видалити старі файли:

- `chat-history.json`
- `rules.json`
- `memory.json`

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
| POST | `/api/message` | Send message |
| WS | `/ws` | Real-time events |

---

## Files Structure

```
ARI/
├── ari_service.py       # Main service
├── agents.py           # LLM agents
├── self_model.py      # Self model
├── belief_system.py   # Beliefs
├── crisis_engine.py   # Crisis
├── self_observer.py  # Meta-awareness
├── goal_system.py    # Goals
├── rule_layer.py    # v7: Rules
├── inquiry_engine.py # v7: Self-inquiry
├── self_modifier.py # v7: Answer analysis
├── run_server.bat   # Server launcher
├── run_frontend.bat # Frontend launcher
├── README.md       # This file
│
├── frontend/
│   ├── index.html    # Frontend UI
│   └── dist/        # Built files
│
└── server/
    ├── server.js    # Node proxy
    ├── package.json
    └── data/       # Persistent data
        ├── chat-history.json
        ├── rules.json
        └── memory.json
```

---

## License

MIT

---

## Credits

- Ollama: https://ollama.ai
- D3.js: https://d3js.org
- React Force Graph: https://github.com/vasturiano/react-force-graph-2d
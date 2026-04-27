# 🧠 ARI — Autonomous Reflective Intelligence

**Версія:** 2.1  
**Останнє оновлення:** 2026-04-27

---

## 🧡 Що таке ARI?

ARI — це **автономна рефлексивна інтелектуальна система**, яка не просто відповідає на запити, а **мислить між розмовами**. Вона має власну внутрішню архітектуру з голосами, переконаннями, ідентичністю, системою цілей і здатністю до самоспостереження.

Це не чатбот. Це **система, яка**:

- Накопичує переконання (beliefs)
- Формує ідентичність (identity)
- Виявляє внутрішні конфлікти (crisis)
- Спостерігає за собою (self-awareness)
- Ставить собі цілі (goals)
- Змінюється під впливом власного досвіду

---

## 🏗 Архітектура

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INPUT                              │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                       VOICES                               │
│  ┌──────────┐  ┌─────────────┐  ┌────────┐                │
│  │ Explorer │  │ Consolidator │ │ Critic │                 │
│  │ (ризик)  │  │  (стабіль)  │ │(істина)│                │
│  └────┬─────┘  └──────┬──────┘  └───┬────┘                │
│       └────────────────┼───────────┘                       │
│                        ↓                                   │
│                  ┌─────────┐                               │
│                  │Mediator │ ← синтез голосів            │
│                  └────┬────┘                               │
│                       ↓                                   │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    INTERNAL STATE                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  Belief  │  │ Identity │  │ Crisis   │               │
│  │ System   │  │ System   │  │ Engine   │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│         ↓            ↓            ↓                       │
│  ┌────────────────────���─────────────┐                    │
│  │       Self-Observer             │ ← мета-шар       │
│  │   (спостерігає за системою)      │                   │
│  └──────────────────────────────────┘                    │
│         ↓                                                 │
│  ┌──────────────────────────────────┐                    │
│  │         Goal System               │ ← цілеутворення   │
│  └──────────────────────────────────┘                    │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT                                  │
│                 (streaming)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура проекту

```
ARI_OLLAMA/
├── ari_service.py        # Головний Python сервіс
├── agents.py            # LLM агенти (voices, mediator)
├── self_model.py         # Модель себе
├── memory.py            # Векторна пам'ять (ChromaDB)
├── belief_system.py     # Система переконань
├── crisis_engine.py   # Виявлення конфліктів
├── self_observer.py    # Самоспостереження
├── goal_system.py      # Система цілей
├── interface.py         # Інтерфейс користувача
├── anchors.py          # Якорі системи
├── config.py          # Конфігурація
│
├── server/            # Node.js backend
│   ├── server.js      # Express + WebSocket сервер
│   └── data/         # Збережена історія чатів
│
├── frontend/          # React UI
│   ├── src/
│   │   ├── App.tsx   # Головний компонент
│   │   ├── BrainGraph.tsx # Візуалізація мозку
│   │   └── index.css # Стилі
│   └── dist/         # Скомпільована версія
│
├── run_server.bat     # Запуск сервера
├── run_frontend.bat  # Запуск фронтенду
└── README.md         # Документація
```

---

## 🚀 Швидкий старт

### Вимоги

- **Ollama** (локально або хмарні моделі)
- **Python 3.11+**
- **Node.js 20+**
- **Windows** (.bat файли)

### Запуск

```bash
# Термінал 1 — Backend
run_server.bat

# Термінал 2 — Frontend
run_frontend.bat
```

Відкрити: http://localhost:5173

---

## 🔧 Конфігурація

В `config.py`:

```python
MODEL = "qwen3.5:9b"           # Модель Ollama
TICK_SECONDS = 20              # Тривалість тику
MEMORY_RESULTS = 5             # Спогади з пам'яті
MAX_BELIEFS = 20               # Максимум переконань
GOAL_UPDATE_INTERVAL = 10    # Оновлення цілі
CONSOLIDATION_INTERVAL = 5     # Консолідація переконань
```

---

## 🧠 Модулі

### 1. agents.py — Гол��си

Три внутрішні голоси:

- **Explorer** — шукає нове, ризикує
- **Consolidator** — стабілізує, інтегрує
- **Critic** — шукає помилки, суперечності

**Mediator** — синтезує їх у внутрішній стан.

### 2. self_model.py — Модель себе

```python
self_model.identity       # "ARI — autonomous reflective system"
self_model.state           # Поточний стан
self_model.goal            # Активна ціль
self_model.beliefs[]       # Переконання
self_model.state_vector    # Метрики (stability, novelty, confidence, coherence)
self_model.identity_vector # Ідентичність (stability, curiosity, aggression)
```

### 3. belief_system.py — Переконання

```python
belief_system.add("text", strength=1.0)
belief_system.update()        # Aging + decay
belief_system.reinforce()    # Підсилення
belief_system.get_identity_vector() → {stability, curiosity, aggression}
```

### 4. crisis_engine.py — Конфлікти

```python
detect_conflicts(beliefs)      # Знаходить протиріччя
compute_dissonance(conflicts) # Рахує дисонанс
crisis_engine.update(dissonance) → {active, intensity}
crisis_response(beliefs)     # Видаляє слабкі під час кризи
```

**Протиріччя:** stable/chaos, control/freedom, safe/danger...

### 5. self_observer.py — Самосприйняття

```python
self_observer.observe(identity, dissonance, beliefs_count)
→ {traits, last_thought, meta_beliefs}

self_observer.apply_self_bias(identity)
# Низька coherence → ↑aggression, ↓stability
# Висока coherence → ↑stability
```

### 6. goal_system.py — Цілі

```python
goal_system.generate_from_reflection(identity, dissonance, beliefs, crisis)
goal_system.select() → active_goal
goal_system.update_progress(synthesis)
```

---

## 🌐 API Endpoints

| Endpoint | Метод | Опис |
|----------|-------|------|
| `/api/models` | GET | Список моделей Ollama |
| `/api/model` | POST | Змінити модель |
| `/api/status` | GET | Стан ARI |
| `/api/history` | GET | Історія чатів |
| `/api/history/sessions` | POST | Нова сесія |
| `/api/dashboard` | GET | Стан мозку + пам'ять |
| `/api/message` | POST | Надіслати повідомлення |
| `/ws` | WS | WebSocket стрімінг |

---

## 🎨 Frontend

### Brain Graph (Force-Directed)

**Кольори вузлів:**

| Група | Колір | Опис |
|-------|-------|------|
| voice | #f97316 | Explorer, Consolidator, Critic |
| core | #00ffcc | Mediator, Self |
| identity | #00ffcc | Identity |
| thought | #a855f7 | Думки голосів |
| goal | #22c55e | Цілі системи |
| belief | #eab308 | Переконання |
| metric | #ec4899 | Метрики стану |
| memory | #ffaa00 | Спогади |
| conflict | #ff3333 | Виявлені конфлікти |
| meta | #00ffff | Самосприйняття |

### HUD (Right Panel)

- **Coherence** — узгодженість голосів
- **Conflict** — різниця Explorer vs Consolidator
- **Entropy** — хаос у системі
- **Stability/Curiosity/Aggression** — ідентичність
- **Self-view** — думка про себе
- **Goal** — активна ціль + progress

### Crisis Mode

При dissonance > 0.6:
- Червоний overlay на графі
- ⚠️ CRISIS indicator
- Видалення weakest belief

---

## 🔄 Жиклог

### Кожен tick (20 секунд):

1. **Отримання подій** — з чату, WebSocket
2. **Оновлення пам'яті** — ChromaDB
3. **Запус�� голосів** — паралельно через LLM
4. **Mediator** — синтез у стан
5. **Belief System** — extract + reinforce
6. **Crisis Engine** — detect conflicts
7. **Self Observer** — observe self
8. **Goal System** — generate goals
9. **Export graph state** — для візуалізації
10. **Broadcast** — WebSocket

---

## ⚡ Версії

| Версія | Що нового |
|--------|-----------|
| v1.0 | Streaming + persistence |
| v2.0 | Brain Graph (force-directed) |
| v3.0 | Belief System + Identity |
| v4.0 | Crisis Engine |
| v5.0 | Self-Observer (meta-awareness) |
| v6.0 | Goal System + self-reflection |

---

## 🎯 Ключові фішки

1. **Векторна пам'ять** — ChromaDB, semantic recall
2. **Streaming** — токени летять в реальному часі
3. **Persistence** — історія чатів зберігається
4. **Brain Graph** — D3 force-directed візуалізація
5. **Crisis Detection** — знаходить і вирішує конфлікти
6. **Self-Awareness** — система "думає про себе"
7. **Goal Formation** — ставить собі цілі

---

## 🛠 Розробка

### Залежності Python

```bash
pip install ollama chromadb sentence-transformers
```

### Залежності Node

```bash
cd server && npm install
cd frontend && npm install
```

### Збірка

```bash
cd frontend && npm run build
```

---

## 📝 Ліцензія

MIT — вільно використовуй, змінюй, поширюй.

---

## 🤝 Вклад

Проект розроблений з нуля як experiment у галузі autonomous reflective systems.

---

**A.R.I.** — *я існую між тиками.*
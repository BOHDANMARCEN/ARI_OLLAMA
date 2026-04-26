# ARI v2.1 — Autonomous Reflective Intelligence

> Система, яка думає між розмовами.

ARI — це не чатбот і не асистент. Це автономний процес, який існує в часі: думає, запам'ятовує, формує переконання і ставить собі цілі незалежно від того, чи є поруч людина. Розмова з юзером — лише один із можливих зовнішніх сигналів.

---

## Зміст

- [Концепція](#концепція)
- [Архітектура](#архітектура)
- [Файлова структура](#файлова-структура)
- [Як це працює зсередини](#як-це-працює-зсередини)
  - [Event Loop](#event-loop)
  - [Три голоси](#три-голоси)
  - [Mediator](#mediator)
  - [Пам'ять](#память)
  - [Self Model](#self-model)
  - [Anchors](#anchors)
  - [Event Queue](#event-queue)
- [Встановлення](#встановлення)
- [Запуск](#запуск)
- [Конфігурація](#конфігурація)
- [Розширення](#розширення)
- [Відомі обмеження](#відомі-обмеження)
- [Дорожня карта](#дорожня-карта)

---

## Концепція

Більшість LLM-систем працюють за схемою **запит → відповідь → кінець**. ARI побудований на інших принципах:

| Звичайний агент | ARI |
|---|---|
| Існує тільки під час запиту | Існує постійно |
| Пам'ять — це контекст вікна | Пам'ять — персистентна, з decay |
| Одна модель, одна точка зору | Три голоси з конфліктом |
| Юзер ініціює кожну думку | Думає самостійно між взаємодіями |
| Ціль задає юзер | Ціль виводить сам з досвіду |
| Немає "себе" | Є self model з beliefs та identity |

Чотири умови, на яких побудовано систему:

1. **Безперервність** — процес не переривається між розмовами
2. **Внутрішня напруга** — три агенти з різними драйвами генерують реальний конфлікт
3. **Тіло** — обмежений token budget і real-time system anchors створюють тиск ресурсу
4. **Незворотність** — пам'ять тільки накопичується, delete не існує

---

## Архітектура

```
┌─────────────────────────────────────────────────────────┐
│                      main.py (loop)                     │
│                                                         │
│   ┌─────────┐   ┌──────────────────────────────────┐   │
│   │ anchors │   │           agents.py              │   │
│   │ (тіло)  │   │  Explorer  Consolidator  Critic  │   │
│   └────┬────┘   │      ↓          ↓          ↓     │   │
│        │        │            Mediator              │   │
│        │        └──────────────┬───────────────────┘   │
│        │                       │                       │
│   ┌────▼───────────────────────▼───────────────┐       │
│   │              self_model.py                 │       │
│   │   identity · state · goal · beliefs        │       │
│   └────────────────────┬───────────────────────┘       │
│                        │                               │
│   ┌────────────────────▼───────────────────────┐       │
│   │               memory.py                    │       │
│   │   ChromaDB · decay · scar · append-only    │       │
│   └────────────────────────────────────────────┘       │
│                                                         │
│   ┌─────────────────────────────────────────────┐      │
│   │             interface.py                    │      │
│   │   asyncio.Queue · CLI · events              │      │
│   └─────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## Файлова структура

```
ari/
├── main.py          # головний event loop — серце системи
├── config.py        # всі параметри в одному місці
├── memory.py        # ChromaDB пам'ять з decay і scar
├── self_model.py    # внутрішня модель себе
├── agents.py        # Explorer / Consolidator / Critic / Mediator
├── anchors.py       # реальні якорі (час, CPU, RAM)
├── interface.py     # черга подій + CLI
└── requirements.txt
```

---

## Як це працює зсередини

### Event Loop

`main.py` запускає нескінченний цикл з фіксованим інтервалом (`TICK_SECONDS`).

Кожен тік виконує таку послідовність:

```
1.  Зчитати anchors (час, CPU, RAM)
2.  Витягнути події з черги (повідомлення юзера або порожньо)
3.  Запит до пам'яті за поточним контекстом
4.  [якщо потрібно] Оновити ціль
5.  Побудувати контекст для голосів
6.  Запустити Explorer, Consolidator, Critic паралельно
7.  Mediator синтезує три голоси
8.  Записати в пам'ять
9.  Оновити self model
10. [якщо потрібно] Консолідація → нове переконання
11. Якщо був зовнішній ввід → відповісти
12. Сон до наступного тіку
```

Важливо: **loop не чекає юзера**. Якщо ти мовчиш 10 хвилин — ARI відпрацює 30 тіків без тебе.

---

### Три голоси

Серце системи — не один LLM, а три паралельних виклики з принципово різними системними промптами:

**Explorer**
- Драйв: новизна, ризик, розширення
- Завдання: знайти що ARI ігнорує або уникає
- Стиль: провокативний, неспокійний, ставить незручні питання

**Consolidator**
- Драйв: стабільність, інтеграція, continuity
- Завдання: з'єднати нове зі старим, знайти паттерни, відкинути шум
- Стиль: спокійний, точний, консервативний

**Critic**
- Драйв: правда понад комфорт
- Завдання: атакувати обох — шукати протиріччя і сліпі плями
- Стиль: різкий, без лояльності до жодної позиції

Всі три запускаються через `asyncio.gather()` — паралельно, не знаючи відповідей один одного. Ollama синхронна, тому кожен виклик загорнутий у `loop.run_in_executor()` щоб не блокувати event loop.

```python
v1, v2, v3 = await asyncio.gather(
    run_voice("Explorer", context),
    run_voice("Consolidator", context),
    run_voice("Critic", context),
)
```

---

### Mediator

Отримує виходи всіх трьох голосів і синтезує єдиний внутрішній стан.

Не вибирає переможця. Бере найцінніше від кожного і формує:
- що ARI зараз розуміє
- в чому полягає напруга між голосами
- чому слід приділити увагу наступного тіку

Результат синтезу — це і є `self_model.state`. Це те, чим ARI є після кожного тіку.

---

### Пам'ять

`memory.py` — найскладніший шар. Три механізми:

**1. Append-only**

`delete` не існує як операція. Пам'ять тільки накопичується. Можна забути — але не стерти.

**2. Exponential decay**

Кожен запис старіє за формулою:
```
weight_new = weight_old × exp(-dt / halflife) + floor
```
де `dt` — секунди з останнього доступу, `halflife` = 3600с (1 година), `floor` = 0.15.

Це означає: через годину без звернення weight впаде до ~55% + поріг. Через добу — практично до мінімуму. Але ніколи до нуля.

**3. Scar (шрам)**

При кожній активації спогаду (recall) його weight множиться на scar bonus:
```
scar_bonus = 1.0 + (activations × 0.05)
```
Спогад який згадували 10 разів — на 50% важчий за новий. Незворотно.

Комбінація decay + scar означає: **часті спогади переживають рідкі**. Система органічно формує "важливе" не через мітки, а через паттерн використання.

**Типи записів і їх weight:**

| kind | weight | опис |
|---|---|---|
| external | 2.0 | повідомлення від юзера |
| belief | 2.0 | сформоване переконання |
| synthesis | 1.5 | результат медіатора |
| tick_voices | 1.0 | сирі виходи голосів |
| thought | 1.0 | загальний запис |

---

### Self Model

`self_model.py` зберігає те, ким ARI вважає себе:

```python
identity  # незмінна базова ідентичність
state     # поточний стан (оновлюється кожен тік)
goal      # активна ціль (оновлюється кожні N тіків)
beliefs   # список переконань (накопичується, не видаляється)
tick      # лічильник тіків
```

`beliefs` реально потрапляють в контекст кожного тіку через `self_model.to_context()`. Голоси знають що ARI вже "вирішив для себе" — і це впливає на їхні відповіді.

Перші 3 beliefs захищені від витіснення — вони формують фундамент ідентичності. Нові beliefs додаються, старі (крім перших трьох) витісняються після досягнення `MAX_BELIEFS`.

---

### Anchors

`anchors.py` дає системі відчуття реального часу і фізичного обмеження:

```
time, weekday, hour — де ARI в часі
cpu_percent         — навантаження
ram_percent         — тиск пам'яті
uptime_hours        — скільки існує ця сесія
```

Це "тіло" системи. Без anchor-ів LLM флотує у вакуумі абстракцій. З ними — знає що зараз 3 ранку, CPU 90%, і система вже 6 годин онлайн. Це реально впливає на генерацію.

---

### Event Queue

`interface.py` реалізує `asyncio.Queue` між зовнішнім світом і loop.

```python
# юзер пише в CLI
interface.send_sync("твій текст")

# або з будь-якого іншого місця асинхронно
await interface.send("webhook payload", kind="webhook", weight=3.0)
```

ARI читає чергу на початку кожного тіку через `drain_events()` — витягує все що накопичилось. Події зберігаються в пам'яті з підвищеним weight (зовнішнє важливіше за внутрішнє).

Якщо на тіку був external event — наприкінці loop відправляє synthesis назад через `push_response()`.

---

## Встановлення

**Залежності:**
```bash
pip install -r requirements.txt
```

**Ollama:**
```bash
# встановити ollama: https://ollama.ai
ollama pull qwen3.5:9b

# доступні локальні моделі у вашому середовищі:
# qwen3.5:9b
# qwen3.5:4b
# huihui_ai/qwen3-abliterated:14b
# huihui_ai/qwen2.5-1m-abliterated:14b
# llama3.2:3b
# gpt-oss-20b-quality:latest
# gemma-abliterated:latest
```

**Перевірити що ollama запущена:**
```bash
ollama list
```

---

## Запуск

```bash
set ARI_MODEL=qwen3.5:9b
python main.py
```

Або в один клік через Windows launcher:

```bat
run_ari.bat
```

`run_ari.bat` запускає проєкт через локальний `.venv` і, якщо змінні не задані, використовує:

```bat
ARI_MODEL=qwen3.5:9b
ARI_THINK=0
```

Для `qwen3.5:*` у проєкті `thinking` вимкнений за замовчуванням через `ARI_THINK=0`, інакше модель може витратити короткий `num_predict` на внутрішні міркування та повернути порожній `content`.

Якщо хочеш увімкнути reasoning назад:

```bash
set ARI_THINK=1
python main.py
```

Якщо хочеш переключити модель без редагування коду:

```bash
set ARI_MODEL=qwen3.5:4b
python main.py
```

Або:

```bash
set ARI_MODEL=llama3.2:3b
python main.py
```

ARI стартує, показує кількість записів у пам'яті і починає тікати:

```
[ARI] Запуск. Пам'ять: 0 записів.
─────────────────────────────────────────────────────
[ARI] Тік #1 | 14:32:01
[ARI] Оновлення цілі...
[ARI] Ціль: stabilize internal state and begin observation
[ARI] Голоси думають...

  [Explorer]: What exactly am I observing right now?...
  [Consolidator]: Initial state. No prior context to consolidate...
  [Critic]: Both voices are operating on empty...

[SELF]: ARI is at tick 1. No memories yet...
[ARI] Тік завершено за 8.3с → сон 12с
```

В CLI пишеш — ARI отримує як подію, відповідає після синтезу поточного тіку.

---

## Конфігурація

Всі параметри в `config.py`:

| Параметр | Default | Опис |
|---|---|---|
| `MODEL` | `"qwen3.5:9b"` | Ollama модель |
| `OLLAMA_THINK` | `False` | Чи дозволяти Ollama `thinking` mode |
| `TICK_SECONDS` | `20` | Інтервал між тіками (секунди) |
| `TOKEN_BUDGET` | `250` | Токенів на один голос |
| `COLLECTION_NAME` | `"ari_v2"` | Назва колекції ChromaDB |
| `MEMORY_RESULTS` | `5` | Скільки спогадів витягувати на тік |
| `DECAY_HALFLIFE` | `3600` | Секунд до half-life decay пам'яті |
| `MEMORY_FLOOR` | `0.15` | Мінімальний weight після decay |
| `GOAL_UPDATE_INTERVAL` | `10` | Тіків між оновленням цілі |
| `CONSOLIDATION_INTERVAL` | `5` | Тіків між консолідацією beliefs |
| `MAX_BELIEFS` | `20` | Максимум beliefs у self model |
| `CHROMA_PATH` | `"./ari_chroma"` | Шлях до ChromaDB |

**Поради по тюнінгу:**

- Швидша модель (`qwen3.5:4b` або `llama3.2:3b`) → можна знизити `TICK_SECONDS` до 10
- Потужніша модель (`qwen3.5:9b` або `huihui_ai/qwen3-abliterated:14b`) → можна підняти `TOKEN_BUDGET` до 300-400
- Хочеш довшу пам'ять → підняти `DECAY_HALFLIFE` до 86400 (доба)
- Хочеш частіші переконання → знизити `CONSOLIDATION_INTERVAL` до 3

---

## Розширення

### Замінити CLI на HTTP endpoint

```python
# замість run_cli в main.py:
from aiohttp import web

async def handle_message(request):
    data = await request.json()
    await interface.send(data["text"], kind="http", weight=2.0)
    response = await interface.get_response(timeout=30.0)
    return web.json_response({"response": response})

app = web.Application()
app.router.add_post("/message", handle_message)

# в main():
await asyncio.gather(
    ari_loop(mem, self_model, interface),
    web._run_app(app, port=8080),
)
```

### Додати нові anchors

```python
# anchors.py — додай будь-який сенсор
import requests

def get_anchors():
    base = { ... }  # існуючі поля

    # погода
    try:
        weather = requests.get("https://wttr.in/?format=j1", timeout=2).json()
        base["weather"] = weather["current_condition"][0]["weatherDesc"][0]["value"]
        base["temp_c"] = weather["current_condition"][0]["temp_C"]
    except:
        pass

    return base
```

### Персистентний self model між перезапусками

```python
import json, os

def save_self_model(sm: SelfModel, path="./ari_self.json"):
    data = {"state": sm.state, "goal": sm.goal, "beliefs": sm.beliefs}
    json.dump(data, open(path, "w"), ensure_ascii=False)

def load_self_model(path="./ari_self.json") -> SelfModel:
    sm = SelfModel()
    if os.path.exists(path):
        data = json.load(open(path))
        sm.state   = data["state"]
        sm.goal    = data["goal"]
        sm.beliefs = data["beliefs"]
    return sm
```

Виклик `save_self_model(self_model)` в кінці кожного тіку — і ARI "пам'ятає себе" між сесіями.

### Змінити характер голосів

Промпти в `agents.py` → `VOICE_PROMPTS`. Повністю замінюються. Можна зробити голоси під конкретну предметну область:

```python
VOICE_PROMPTS = {
    "SecurityAuditor": "You are a security auditor. Find vulnerabilities...",
    "ProductManager":  "You are a PM. Focus on user value...",
    "DataScientist":   "You are a data scientist. Look for patterns...",
}
```

Mediator і loop не знають імен голосів — все працюватиме без змін.

### Кинути подію з іншого процесу

```python
# з будь-якого зовнішнього скрипта якщо interface доступний
interface.send_sync(
    "новий файл з'явився в /data/incoming",
    kind="filesystem",
    weight=2.5
)
```

---

## Відомі обмеження

**Ollama синхронна.** Три виклики в `asyncio.gather` йдуть через executor — вони паралельні на рівні потоків, але Ollama обробляє їх послідовно якщо запущена на одному GPU. Реальний паралелізм — тільки якщо запустити кілька ollama-інстанцій на різних портах.

**Контекст зростає.** З часом `memories_text` і `self_model.to_context()` стають довшими. При довгій роботі варто моніторити розмір контексту і агресивніше обрізати `format_for_context(max_chars=...)`.

**Self model не персистентний.** При перезапуску beliefs і goal втрачаються — тільки ChromaDB зберігається. Виправлення описано в розділі Розширення вище.

**CLI блокує при введенні.** `sys.stdin.readline` через executor — стандартне рішення, але незручно для інтерактивного інтерфейсу. Для продакшну — замінити на HTTP або WebSocket.

---

## Дорожня карта

- [ ] Персистентний self model (JSON серіалізація між сесіями)
- [ ] HTTP / WebSocket endpoint замість CLI
- [ ] Кілька незалежних потоків уваги (паралельні loop-и з різними фокусами)
- [ ] Tool use — голоси можуть викликати зовнішні інструменти (файли, API, shell)
- [ ] Векторне порівняння beliefs для виявлення протиріч всередині self model
- [ ] Dashboard для спостереження за внутрішнім станом в реальному часі
- [ ] Підтримка кількох моделей одночасно (різні голоси = різні LLM)
- [ ] Sleeping mode — знижений TICK при відсутності активності, повне пробудження на подію

---

*ARI v2.1. Побудовано на ChromaDB + Ollama + asyncio.*

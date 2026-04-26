# ─────────────────────────────────────────────
# ARI v2.1 — config.py
# ─────────────────────────────────────────────

import os


MODEL = os.getenv("ARI_MODEL", "qwen3.5:9b")  # default Ollama model
OLLAMA_THINK = os.getenv("ARI_THINK", "0") == "1"  # disable thinking by default
TICK_SECONDS = 20               # інтервал між тіками
TOKEN_BUDGET = 250              # токенів на голос
COLLECTION_NAME = "ari_v2"     # chromadb collection
MEMORY_RESULTS = 5             # спогадів на тік
DECAY_HALFLIFE = 3600          # секунд до half-life decay (1 год)
MEMORY_FLOOR = 0.15            # мінімальний weight після decay
GOAL_UPDATE_INTERVAL = 10      # тіків між оновленням цілі
CONSOLIDATION_INTERVAL = 5     # тіків між консолідацією
MAX_BELIEFS = 20               # максимум beliefs у SelfModel
CHROMA_PATH = "./ari_chroma"   # де зберігати chromadb

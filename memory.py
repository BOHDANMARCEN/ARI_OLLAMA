# ─────────────────────────────────────────────
# ARI v2.1 — memory.py
# ─────────────────────────────────────────────

import math
import time
import uuid

import chromadb

from config import (
    CHROMA_PATH, COLLECTION_NAME,
    DECAY_HALFLIFE, MEMORY_FLOOR, MEMORY_RESULTS
)


class Memory:
    """
    Append-only weighted memory з exponential decay.
    Delete не існує — тільки fade.
    Кожна активація спогаду підвищує його weight (шрам).
    """

    def __init__(self):
        self.db = chromadb.PersistentClient(path=CHROMA_PATH)
        self.col = self.db.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    # ── запис ──────────────────────────────────

    def store(self, text: str, kind: str = "thought", weight: float = 1.0) -> str:
        doc_id = str(uuid.uuid4())
        self.col.add(
            documents=[text],
            ids=[doc_id],
            metadatas=[{
                "kind": kind,
                "weight": weight,
                "created": time.time(),
                "last_access": time.time(),
                "activations": 0,
            }]
        )
        return doc_id

    # ── витяг ──────────────────────────────────

    def recall(self, query: str, n: int = MEMORY_RESULTS) -> list[dict]:
        total = self.col.count()
        if total == 0:
            return []

        n = min(n, total)
        res = self.col.query(query_texts=[query], n_results=n)
        now = time.time()
        out = []

        for i, doc_id in enumerate(res["ids"][0]):
            meta = res["metadatas"][0][i]
            text = res["documents"][0][i]

            # exponential decay з моменту останнього доступу
            dt = now - meta["last_access"]
            decay = math.exp(-dt / DECAY_HALFLIFE)
            new_weight = max(meta["weight"] * decay + MEMORY_FLOOR, MEMORY_FLOOR)

            # активація = незворотне підвищення + оновлення часу
            new_activations = meta["activations"] + 1
            scar_bonus = 1.0 + (new_activations * 0.05)  # шрам
            new_weight *= scar_bonus

            self.col.update(
                ids=[doc_id],
                metadatas=[{
                    **meta,
                    "weight": new_weight,
                    "last_access": now,
                    "activations": new_activations,
                }]
            )

            out.append({
                "id": doc_id,
                "text": text,
                "weight": new_weight,
                "kind": meta["kind"],
                "activations": new_activations,
            })

        return sorted(out, key=lambda x: x["weight"], reverse=True)

    # ── утиліти ────────────────────────────────

    def count(self) -> int:
        return self.col.count()

    def format_for_context(self, memories: list[dict], max_chars: int = 800) -> str:
        """Форматує спогади в рядок для LLM-контексту."""
        lines = []
        total = 0
        for m in memories:
            tag = f"[{m['kind']} w={m['weight']:.2f}]"
            line = f"{tag} {m['text'][:200]}"
            if total + len(line) > max_chars:
                break
            lines.append(line)
            total += len(line)
        return "\n".join(lines) if lines else "(empty)"

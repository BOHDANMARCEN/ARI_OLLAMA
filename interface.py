# ─────────────────────────────────────────────
# ARI v2.1 — interface.py
# ─────────────────────────────────────────────

import asyncio
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    """Зовнішня подія для ARI."""
    kind: str          # "user_message" | "file" | "webhook" | "system"
    payload: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    weight: float = 2.0  # зовнішні події важливіші за внутрішні думки


class ARIInterface:
    """
    Черга подій між зовнішнім світом і event loop.
    ARI читає з неї кожен тік.
    Можна кидати будь-що: повідомлення, файли, webhook-и.
    """

    def __init__(self):
        self._in_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._out_queue: asyncio.Queue[str] = asyncio.Queue()

    # ── зовнішній → ARI ────────────────────────

    async def send(self, text: str, kind: str = "user_message", weight: float = 2.0):
        event = Event(kind=kind, payload=text, weight=weight)
        await self._in_queue.put(event)

    def send_sync(self, text: str, kind: str = "user_message", weight: float = 2.0):
        """Синхронна версія для CLI."""
        event = Event(kind=kind, payload=text, weight=weight)
        self._in_queue.put_nowait(event)

    # ── ARI читає події ─────────────────────────

    def drain_events(self) -> list[Event]:
        """Витягнути всі події з черги (не чекати)."""
        events = []
        while not self._in_queue.empty():
            try:
                events.append(self._in_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return events

    # ── ARI → зовнішній ────────────────────────

    async def push_response(self, text: str):
        await self._out_queue.put(text)

    async def get_response(self, timeout: float = 5.0) -> Optional[str]:
        try:
            return await asyncio.wait_for(self._out_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None


# ─────────────────────────────────────────────
# CLI RUNNER
# ─────────────────────────────────────────────

async def run_cli(interface: ARIInterface):
    """
    Простий CLI. Чекає ввід від юзера,
    кидає в чергу, чекає відповідь.
    Не блокує event loop — використовує executor.
    """
    loop = asyncio.get_event_loop()
    print("\n" + "=" * 55)
    print("  ARI v2.1 — Autonomous Reflective Intelligence")
    print("  'quit' — вихід | Enter — надіслати повідомлення")
    print("=" * 55 + "\n")

    while True:
        try:
            raw = await loop.run_in_executor(None, sys.stdin.readline)
            text = raw.strip()

            if not text:
                continue
            if text.lower() in ("quit", "exit", "q"):
                print("[ARI] Завершення. Пам'ять збережена.")
                return

            interface.send_sync(text)
            print(f"[YOU → ARI]: {text}")

            # чекаємо відповіді до 60с
            response = await interface.get_response(timeout=60.0)
            if response:
                print(f"\n[ARI → YOU]:\n{response}\n")
            else:
                print("[ARI]: (відповідь не сформована на цьому тіку)\n")

        except (EOFError, KeyboardInterrupt):
            print("\n[ARI] Переривання. Виходжу.")
            return
        except Exception as e:
            print(f"[CLI ERROR]: {e}")

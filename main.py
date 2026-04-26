# ─────────────────────────────────────────────
# ARI v2.1 — main.py
# Autonomous Reflective Intelligence
#
# Запуск:
#   pip install chromadb ollama psutil
#   set ARI_MODEL=qwen3.5:9b
#   python main.py
# ─────────────────────────────────────────────

import asyncio
import time
from datetime import datetime

from config import (
    TICK_SECONDS,
    MEMORY_RESULTS,
    GOAL_UPDATE_INTERVAL,
    CONSOLIDATION_INTERVAL,
)
from memory import Memory
from self_model import SelfModel
from agents import (
    run_all_voices,
    run_mediator,
    derive_goal,
    extract_belief,
)
from anchors import get_anchors, format_anchors
from interface import ARIInterface, run_cli


# ─────────────────────────────────────────────
# ГОЛОВНИЙ EVENT LOOP
# ─────────────────────────────────────────────

async def ari_loop(mem: Memory, self_model: SelfModel, interface: ARIInterface):
    print(f"[ARI] Запуск. Пам'ять: {mem.count()} записів.")

    while True:
        tick_start = time.time()
        tick = self_model.tick + 1

        print(f"\n{'-' * 55}")
        print(f"[ARI] Тік #{tick} | {datetime.now().strftime('%H:%M:%S')}")

        # ── 1. Зовнішні якорі ──────────────────
        anchors = get_anchors()
        anchors_str = format_anchors(anchors)

        # ── 2. Зовнішні події від юзера ────────
        external_events = interface.drain_events()
        has_user_input = bool(external_events)

        for event in external_events:
            mem.store(
                f"[{event.kind.upper()}]: {event.payload}",
                kind="external",
                weight=event.weight
            )

        # ── 3. Запит до пам'яті ────────────────
        query = (
            external_events[0].payload
            if external_events
            else self_model.goal
        )
        memories = mem.recall(query, n=MEMORY_RESULTS)
        memories_text = mem.format_for_context(memories)

        # ── 4. Оновити ціль (рідко) ────────────
        if tick % GOAL_UPDATE_INTERVAL == 0 or tick == 1:
            print("[ARI] Оновлення цілі...")
            new_goal = await derive_goal(memories_text, self_model.to_context())
            self_model.update_goal(new_goal)
            print(f"[ARI] Ціль: {self_model.goal}")

        # ── 5. Будуємо контекст для голосів ────
        context = (
            f"ANCHORS: {anchors_str}\n\n"
            f"SELF MODEL:\n{self_model.to_context()}\n\n"
            f"MEMORIES:\n{memories_text}\n\n"
        )
        if external_events:
            events_summary = "\n".join(
                f"  [{e.kind}]: {e.payload}" for e in external_events
            )
            context += f"EXTERNAL EVENTS THIS TICK:\n{events_summary}\n"

        # ── 6. Запускаємо три голоси паралельно ─
        print("[ARI] Голоси думають...")
        voices = await run_all_voices(context)

        for name, resp in voices.items():
            print(f"\n  [{name}]: {resp[:200]}{'...' if len(resp) > 200 else ''}")

        # ── 7. Mediator синтезує ────────────────
        print("\n[ARI] Синтез...")
        synthesis = await run_mediator(voices, self_model.to_context())
        print(f"\n[SELF]: {synthesis[:300]}{'...' if len(synthesis) > 300 else ''}")

        # ── 8. Зберегти в пам'ять ──────────────
        voices_dump = "\n".join(
            f"[{n}]: {r}" for n, r in voices.items()
        )
        mem.store(voices_dump, kind="tick_voices", weight=1.0)
        mem.store(synthesis, kind="synthesis", weight=1.5)

        # ── 9. Оновити self model ───────────────
        self_model.update_state(synthesis)

        # ── 10. Консолідація (рідко) ────────────
        if tick % CONSOLIDATION_INTERVAL == 0:
            print("[ARI] Консолідація...")
            deep_memories = mem.recall("important patterns beliefs", n=10)
            deep_text = mem.format_for_context(deep_memories, max_chars=1200)
            belief = await extract_belief(deep_text)
            self_model.add_belief(belief)
            mem.store(belief, kind="belief", weight=2.0)
            print(f"[ARI] Нове переконання: {belief}")

        # ── 11. Відповідь юзеру (якщо був ввід) ─
        if has_user_input:
            await interface.push_response(synthesis)

        # ── 12. Сон до наступного тіку ──────────
        elapsed = time.time() - tick_start
        sleep_time = max(0.0, TICK_SECONDS - elapsed)
        print(f"\n[ARI] Тік завершено за {elapsed:.1f}с → сон {sleep_time:.0f}с")
        await asyncio.sleep(sleep_time)


# ─────────────────────────────────────────────
# ТОЧКА ВХОДУ
# ─────────────────────────────────────────────

async def main():
    mem = Memory()
    self_model = SelfModel()
    interface = ARIInterface()

    # запускаємо loop і CLI паралельно
    await asyncio.gather(
        ari_loop(mem, self_model, interface),
        run_cli(interface),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[ARI] Зупинено вручну. До побачення.")

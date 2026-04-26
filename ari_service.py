import asyncio
import json
import sys
import time
from datetime import datetime

from anchors import format_anchors, get_anchors
from agents import derive_goal, extract_belief, run_all_voices, run_mediator
from config import CONSOLIDATION_INTERVAL, GOAL_UPDATE_INTERVAL, MEMORY_RESULTS, MODEL, TICK_SECONDS
from interface import ARIInterface
from memory import Memory
from self_model import SelfModel


def _configure_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def emit(event_type: str, **payload) -> None:
    sys.stdout.write(json.dumps({"type": event_type, **payload}, ensure_ascii=False) + "\n")
    sys.stdout.flush()


async def stdin_bridge(interface: ARIInterface, shutdown_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()

    while not shutdown_event.is_set():
        raw = await loop.run_in_executor(None, sys.stdin.readline)
        if raw == "":
            shutdown_event.set()
            return

        raw = raw.strip()
        if not raw:
            continue

        try:
            message = json.loads(raw)
        except json.JSONDecodeError as exc:
            emit("error", message=f"Invalid JSON input: {exc}")
            continue

        msg_type = message.get("type")
        if msg_type == "user_message":
            text = (message.get("text") or "").strip()
            if text:
                await interface.send(text, kind="user_message", weight=2.0)
                emit("message_received", text=text)
        elif msg_type == "shutdown":
            shutdown_event.set()
            return
        elif msg_type == "ping":
            emit("pong", ts=time.time())
        else:
            emit("error", message=f"Unsupported message type: {msg_type}")


async def ari_loop_service(mem: Memory, self_model: SelfModel, interface: ARIInterface, shutdown_event: asyncio.Event) -> None:
    emit("status", phase="started", model=MODEL, memory_count=mem.count())

    while not shutdown_event.is_set():
        tick_start = time.time()
        tick = self_model.tick + 1
        emit("tick_start", tick=tick, timestamp=datetime.now().isoformat())

        anchors = get_anchors()
        anchors_str = format_anchors(anchors)

        external_events = interface.drain_events()
        has_user_input = bool(external_events)

        for event in external_events:
            mem.store(f"[{event.kind.upper()}]: {event.payload}", kind="external", weight=event.weight)

        query = external_events[0].payload if external_events else self_model.goal
        memories = mem.recall(query, n=MEMORY_RESULTS)
        memories_text = mem.format_for_context(memories)

        if tick % GOAL_UPDATE_INTERVAL == 0 or tick == 1:
            new_goal = await derive_goal(memories_text, self_model.to_context())
            self_model.update_goal(new_goal)
            emit("goal_updated", tick=tick, goal=self_model.goal)

        context = (
            f"ANCHORS: {anchors_str}\n\n"
            f"SELF MODEL:\n{self_model.to_context()}\n\n"
            f"MEMORIES:\n{memories_text}\n\n"
        )
        if external_events:
            events_summary = "\n".join(f"  [{e.kind}]: {e.payload}" for e in external_events)
            context += f"EXTERNAL EVENTS THIS TICK:\n{events_summary}\n"

        voices = await run_all_voices(context)
        for name, resp in voices.items():
            emit("voice", tick=tick, name=name, text=resp)

        synthesis = await run_mediator(voices, self_model.to_context())
        emit("synthesis", tick=tick, text=synthesis)

        voices_dump = "\n".join(f"[{name}]: {resp}" for name, resp in voices.items())
        mem.store(voices_dump, kind="tick_voices", weight=1.0)
        mem.store(synthesis, kind="synthesis", weight=1.5)

        self_model.update_state(synthesis)

        if tick % CONSOLIDATION_INTERVAL == 0:
            deep_memories = mem.recall("important patterns beliefs", n=10)
            deep_text = mem.format_for_context(deep_memories, max_chars=1200)
            belief = await extract_belief(deep_text)
            self_model.add_belief(belief)
            mem.store(belief, kind="belief", weight=2.0)
            emit("belief", tick=tick, text=belief)

        if has_user_input:
            await interface.push_response(synthesis)
            emit("response", tick=tick, text=synthesis)

        elapsed = time.time() - tick_start
        sleep_time = max(0.0, TICK_SECONDS - elapsed)
        emit("tick_complete", tick=tick, elapsed=elapsed, sleep_time=sleep_time)

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=sleep_time)
        except asyncio.TimeoutError:
            pass


async def main() -> None:
    _configure_stdio()

    mem = Memory()
    self_model = SelfModel()
    interface = ARIInterface()
    shutdown_event = asyncio.Event()

    try:
        await asyncio.gather(
            ari_loop_service(mem, self_model, interface, shutdown_event),
            stdin_bridge(interface, shutdown_event),
        )
    except Exception as exc:
        emit("error", message=str(exc))
        raise
    finally:
        emit("status", phase="stopped", model=MODEL, tick=self_model.tick)


if __name__ == "__main__":
    asyncio.run(main())

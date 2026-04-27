import asyncio
import json
import sys
import time
from datetime import datetime

from anchors import format_anchors, get_anchors
from agents import derive_goal, extract_belief, run_all_voices, run_mediator, stream_mediator
from belief_system import BeliefSystem
from crisis_engine import CrisisEngine, detect_conflicts, compute_dissonance, crisis_response, update_identity_from_crisis
from goal_system import GoalSystem
from self_observer import SelfObserver
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
            session_id = message.get("session_id")
            if text:
                await interface.send(text, kind="user_message", weight=2.0, session_id=session_id)
                emit("message_received", text=text, session_id=session_id)
        elif msg_type == "shutdown":
            shutdown_event.set()
            return
        elif msg_type == "ping":
            emit("pong", ts=time.time())
        else:
            emit("error", message=f"Unsupported message type: {msg_type}")


async def ari_loop_service(mem: Memory, self_model: SelfModel, belief_system: BeliefSystem, crisis_engine: CrisisEngine, goal_system: GoalSystem, self_observer: SelfObserver, interface: ARIInterface, shutdown_event: asyncio.Event) -> None:
    emit("status", phase="started", model=MODEL, memory_count=mem.count())

    while not shutdown_event.is_set():
        tick_start = time.time()
        tick = self_model.tick + 1
        emit("tick_start", tick=tick, timestamp=datetime.now().isoformat())

        anchors = get_anchors()
        anchors_str = format_anchors(anchors)

        external_events = interface.drain_events()
        has_user_input = bool(external_events)
        response_session_id = external_events[0].session_id if external_events else None

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

        voices = await run_all_voices(context, meta_context, goal_context)
        
        for name, resp in voices.items():
            emit("voice", tick=tick, name=name, text=resp)

        if has_user_input and response_session_id:
            emit("response_start", tick=tick, session_id=response_session_id)

            async def on_token(token: str) -> None:
                emit("response_token", tick=tick, session_id=response_session_id, token=token)

            synthesis = await stream_mediator(voices, self_model.to_context(), on_token)
            emit("response_end", tick=tick, session_id=response_session_id)
        else:
            synthesis = await run_mediator(voices, self_model.to_context())

        emit("synthesis", tick=tick, text=synthesis)

        voices_dump = "\n".join(f"[{name}]: {resp}" for name, resp in voices.items())
        mem.store(voices_dump, kind="tick_voices", weight=1.0)
        mem.store(synthesis, kind="synthesis", weight=1.5)

        self_model.update_state(synthesis, voices=voices, had_user_input=has_user_input)

        belief_system.update()
        extracted = belief_system.extract_from_text(synthesis)
        for b in extracted:
            belief_system.add(b, strength=0.8)
        belief_system.reinforce(synthesis)

        if tick % CONSOLIDATION_INTERVAL == 0:
            deep_memories = mem.recall("important patterns beliefs", n=10)
            deep_text = mem.format_for_context(deep_memories, max_chars=1200)
            belief = await extract_belief(deep_text)
            if belief:
                belief_system.add(belief, strength=1.2)
                self_model.add_belief(belief)
                mem.store(belief, kind="belief", weight=2.0)
                emit("belief", tick=tick, text=belief)

        self_model.update_identity_from_belief_system(belief_system)

        conflicts = detect_conflicts(belief_system.get_all())
        dissonance = compute_dissonance(conflicts)
        crisis_state = crisis_engine.update(dissonance)
        
        if crisis_state.get("triggered"):
            removed = crisis_response(belief_system.beliefs, max_remove=1)
            if removed:
                emit("crisis", tick=tick, message="Belief removed due to conflict", removed=[getattr(r, 'text', str(r)) for r in removed])
        
        if crisis_engine.active:
            identity = self_model.identity_vector
            updated_identity = update_identity_from_crisis(identity, crisis_engine.get_state())
            self_model.identity_vector = updated_identity

        meta_state = self_observer.observe(
            self_model.identity_vector,
            dissonance,
            len(belief_system.get_all()),
            crisis_engine.active,
        )
        
        self_observer.apply_self_bias(self_model.identity_vector)

        if tick % 3 == 0:
            new_observations = goal_system.generate_from_reflection(
                self_model.identity_vector,
                dissonance,
                len(belief_system.get_all()),
                crisis_engine.active,
            )
            for obs in new_observations[:2]:
                goal_system.add(obs, priority=0.9)

        goal_system.update()
        active_goal = goal_system.select()

        if synthesis:
            goal_system.update_progress(synthesis)

        if active_goal:
            emit("goal", tick=tick, text=active_goal.text, progress=active_goal.progress)

        goal_context = goal_system.apply_goals_to_context()
        meta_context = self_observer.get_meta_context()

        emit(
            "brain_snapshot",
            tick=tick,
            snapshot=self_model.snapshot(),
            voices=voices,
        )

        graph_state = self_model.export_graph_state(voices, memories, belief_system, crisis_engine, self_observer, goal_system)
        emit("brain_graph", tick=tick, graph=graph_state)
        emit(
            "memory_snapshot",
            tick=tick,
            query=query,
            total=mem.count(),
            recalled=memories,
            recent=mem.recent(12),
        )

        if has_user_input:
            await interface.push_response(synthesis)
            emit("response", tick=tick, text=synthesis, session_id=response_session_id)

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
    belief_system = BeliefSystem()
    crisis_engine = CrisisEngine()
    goal_system = GoalSystem()
    self_observer = SelfObserver()
    interface = ARIInterface()
    shutdown_event = asyncio.Event()

    try:
        await asyncio.gather(
            ari_loop_service(mem, self_model, belief_system, crisis_engine, goal_system, self_observer, interface, shutdown_event),
            stdin_bridge(interface, shutdown_event),
        )
    except Exception as exc:
        emit("error", message=str(exc))
        raise
    finally:
        emit("status", phase="stopped", model=MODEL, tick=self_model.tick)


if __name__ == "__main__":
    asyncio.run(main())

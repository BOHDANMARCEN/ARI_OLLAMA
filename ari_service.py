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
from inquiry_engine import InquiryEngine
from rule_layer import RuleLayer
from self_modifier import answer_self_inquiry, parse_modifications, summarize_answer
from self_observer import SelfObserver
from config import CONSOLIDATION_INTERVAL, GOAL_UPDATE_INTERVAL, MEMORY_RESULTS, MODEL, TICK_SECONDS
from interface import ARIInterface
from memory import Memory
from self_model import SelfModel
from mood_layer import Mood
from preferences import Preferences
from style_tracker import StyleTracker
from spontaneous_thought import SpontaneousThought
from continuity_engine import ContinuityEngine
from narrative_memory import NarrativeMemory
from self_priorities import SelfPriorities
from identity_defense import IdentityDefense
from long_projects import LongProjects


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


async def ari_loop_service(mem: Memory, self_model: SelfModel, belief_system: BeliefSystem, crisis_engine: CrisisEngine, goal_system: GoalSystem, self_observer: SelfObserver, rule_layer: RuleLayer, inquiry_engine: InquiryEngine, interface: ARIInterface, shutdown_event: asyncio.Event, mood: Mood, preferences: Preferences, style_tracker: StyleTracker, spontaneous: SpontaneousThought, continuity: ContinuityEngine, narrative: NarrativeMemory, priorities: SelfPriorities, defense: IdentityDefense, long_projects: LongProjects) -> None:
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

        goal_context = ""
        meta_context = ""
        rule_context = ""

        voices = await run_all_voices(context, meta_context, goal_context, rule_context)
        
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

        # v8: Emergence - Spontaneous thought (if no user input)
        spontaneous_topic = ""
        if not has_user_input and tick >= 3:
            if spontaneous.should_think(has_user_input, tick):
                goal_list = [{"text": g.text, "progress": g.progress} for g in goal_system.goals[:3]]
                belief_list = [{"text": b.text, "strength": getattr(b, 'strength', 0.5)} for b in belief_system.get_all()[:5]]
                spontaneous_topic = spontaneous.generate(memories, goal_list, belief_list, crisis_engine.active)
                emit("spontaneous", tick=tick, topic=spontaneous_topic)
                context += f"\nSPONTANEOUS THOUGHT: {spontaneous_topic}\n"

        # v8: Emergence - Update preferences from synthesis
        if synthesis:
            preference_changes = preferences.reinforce(synthesis)
            style_traits = style_tracker.analyze(synthesis)

        # v8: Emergence - Mood update
        progress = active_goal.progress if active_goal else 0.0
        crisis_intensity = crisis_state.get("intensity", 0.0) if crisis_state else 0.0
        mood.update(crisis_intensity, progress, has_user_input)

        # v9: Continuity - record self across time
        continuity.record(
            self_model.identity_vector,
            mood.valence,
            active_goal.text if active_goal else None,
            synthesis,
        )

        # v9: Narrative memory - add story events
        if crisis_engine.active:
            narrative.add_crisis_resolution("internal conflict resolved")
        elif tick % 20 == 0:
            narrative.add_event("checkpoint", f"tick {tick}: ongoing", 0.5)

        # v9: Identity defense - assess threats
        if synthesis:
            threat_result = defense.assess_threat(synthesis, self_model.identity_vector)
            if threat_result.get("threat"):
                defense_result = defense.defend(True)
                emit("defense", tick=tick, level=defense_result.get("magnitude", 0))
            else:
                defense.relax()

        # v9: Long projects - update progress
        if synthesis:
            long_projects.update_all(synthesis)

        # Self-Inquiry: every 5 ticks OR crisis
        rule_state = None
        inquiry_answer = None
        if inquiry_engine.should_inquire(tick, crisis_engine.active):
            question = inquiry_engine.generate_question(
                tick,
                crisis_engine.active,
                self_model.identity_vector,
                goal_system.get_top_goals(2),
            )
            if question:
                emit("inquiry", tick=tick, question=question)
                # Async LLM pass for answer
                try:
                    context = self_model.to_context()
                    inquiry_answer = await answer_self_inquiry(question, context)
                    emit("inquiry_answer", tick=tick, answer=inquiry_answer, question=question)
                    
                    # Apply rule modifications
                    modifications = parse_modifications(inquiry_answer)
                    for key, value in modifications.items():
                        if value.startswith("+") and value.endswith("%"):
                            rule_layer.modify(key, 0.03)
                        elif value.startswith("-") and value.endswith("%"):
                            rule_layer.modify(key, -0.03)
                    rule_state = rule_layer.get_state()
                except Exception as e:
                    emit("error", message=f"Inquiry failed: {e}")

        goal_context = goal_system.apply_goals_to_context()
        meta_context = self_observer.get_meta_context()

        emit(
            "brain_snapshot",
            tick=tick,
            snapshot=self_model.snapshot(),
            voices=voices,
        )

        graph_state = self_model.export_graph_state(voices, memories, belief_system, crisis_engine, self_observer, goal_system, rule_layer, inquiry_engine, mood, preferences, style_tracker, spontaneous, continuity, narrative, priorities, defense, long_projects)
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
    rule_layer = RuleLayer()
    inquiry_engine = InquiryEngine()
    mood = Mood()
    preferences = Preferences()
    style_tracker = StyleTracker()
    spontaneous = SpontaneousThought()
    continuity = ContinuityEngine()
    narrative = NarrativeMemory()
    priorities = SelfPriorities()
    defense = IdentityDefense()
    long_projects = LongProjects()
    interface = ARIInterface()
    shutdown_event = asyncio.Event()

    try:
        await asyncio.gather(
            ari_loop_service(mem, self_model, belief_system, crisis_engine, goal_system, self_observer, rule_layer, inquiry_engine, interface, shutdown_event, mood, preferences, style_tracker, spontaneous, continuity, narrative, priorities, defense, long_projects),
            stdin_bridge(interface, shutdown_event),
        )
    except Exception as exc:
        emit("error", message=str(exc))
        raise
    finally:
        emit("status", phase="stopped", model=MODEL, tick=self_model.tick)


if __name__ == "__main__":
    asyncio.run(main())

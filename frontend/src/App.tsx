import { useEffect, useMemo, useRef, useState } from "react";

import BrainGraph from "./BrainGraph";

type ModelInfo = {
  name: string;
  size?: number;
};

type BackendStatus = {
  type: string;
  model: string;
  state: string;
  lastError: string | null;
  lastTick: number;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  title: string;
  text: string;
  createdAt?: string;
};

type ChatSession = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
};

type ActivityItem = {
  id: string;
  label: string;
  detail: string;
};

type BrainSnapshot = {
  tick: number;
  snapshot: {
    state: string;
    goal: string;
    beliefs: string[];
    tick: number;
    uptime: number;
    state_vector: Record<string, number>;
  };
  voices: Record<string, string>;
};

type MemoryItem = {
  id: string;
  text: string;
  kind: string;
  weight: number;
  activations?: number;
};

type MemorySnapshot = {
  tick: number;
  query: string;
  total: number;
  recalled: MemoryItem[];
  recent: MemoryItem[];
};

const initialStatus: BackendStatus = {
  type: "status_snapshot",
  model: "qwen3.5:9b",
  state: "connecting",
  lastError: null,
  lastTick: 0,
};

function formatBytes(size?: number) {
  if (!size) {
    return "cloud";
  }

  const gb = size / 1024 ** 3;
  return `${gb.toFixed(1)} GB`;
}

function sortSessions(sessions: ChatSession[]) {
  return [...sessions].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export default function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState("");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState("qwen3.5:9b");
  const [status, setStatus] = useState<BackendStatus>(initialStatus);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [brain, setBrain] = useState<BrainSnapshot | null>(null);
  const [memory, setMemory] = useState<MemorySnapshot | null>(null);
  const [input, setInput] = useState("");
  const [switchingModel, setSwitchingModel] = useState(false);
  const [loadingModels, setLoadingModels] = useState(true);
  const [composerDisabled, setComposerDisabled] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const currentSession = useMemo(
    () => sessions.find((session) => session.id === currentSessionId) ?? null,
    [sessions, currentSessionId],
  );

  const messages = currentSession?.messages ?? [];
  const sortedSessions = useMemo(() => sortSessions(sessions), [sessions]);
  const voiceCards = useMemo(() => Object.entries(brain?.voices ?? {}), [brain]);

  const connectionLabel = useMemo(() => {
    if (switchingModel) {
      return "Restarting ARI";
    }
    if (status.state === "running") {
      return "Live";
    }
    if (status.state === "starting" || status.state === "stopping") {
      return "Transitioning";
    }
    return "Disconnected";
  }, [status.state, switchingModel]);

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    const wsUrl = "ws://localhost:3000/ws";
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      handleSocketEvent(payload);
    };

    socket.onclose = () => {
      setStatus((prev) => ({ ...prev, state: "stopped" }));
    };

    return () => socket.close();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function bootstrap() {
    await Promise.all([loadModels(), loadStatus(), loadHistory(), loadDashboard()]);
  }

  async function loadModels() {
    setLoadingModels(true);
    const response = await fetch("/api/models");
    const data = await response.json();
    setModels(data.models || []);
    setSelectedModel(data.currentModel || data.models?.[0]?.name || "qwen3.5:9b");
    setLoadingModels(false);
  }

  async function loadStatus() {
    const response = await fetch("/api/status");
    const data = await response.json();
    setStatus(data);
    setComposerDisabled(data.state !== "running");
  }

  async function loadHistory() {
    const response = await fetch("/api/history");
    const data = await response.json();
    const nextSessions = data.sessions || [];
    setSessions(nextSessions);
    setCurrentSessionId((prev) => prev || nextSessions[0]?.id || "");
  }

  async function loadDashboard() {
    const response = await fetch("/api/dashboard");
    const data = await response.json();
    if (data.status) {
      setStatus(data.status);
    }
    if (data.brain) {
      setBrain(data.brain);
    }
    if (data.memory) {
      setMemory(data.memory);
    }
  }

  function pushActivity(label: string, detail: string) {
    setActivity((prev) => [{ id: crypto.randomUUID(), label, detail }, ...prev].slice(0, 20));
  }

  function patchSessionMessage(sessionId: string, messageId: string, updater: (message: ChatMessage) => ChatMessage) {
    setSessions((prev) => prev.map((session) => {
      if (session.id !== sessionId) {
        return session;
      }
      return {
        ...session,
        messages: session.messages.map((message) => (
          message.id === messageId ? updater(message) : message
        )),
      };
    }));
  }

  function handleSocketEvent(payload: Record<string, unknown>) {
    switch (payload.type) {
      case "status_snapshot":
        setStatus(payload as BackendStatus);
        setSwitchingModel(false);
        setComposerDisabled(payload.state !== "running");
        pushActivity("System", `${payload.state} on ${payload.model}`);
        break;
      case "history_snapshot": {
        const nextSessions = (payload.sessions as ChatSession[]) || [];
        setSessions(nextSessions);
        setCurrentSessionId((prev) => prev || nextSessions[0]?.id || "");
        break;
      }
      case "dashboard_snapshot":
        if (payload.status) {
          setStatus(payload.status as BackendStatus);
        }
        if (payload.brain) {
          setBrain(payload.brain as BrainSnapshot);
        }
        if (payload.memory) {
          setMemory(payload.memory as MemorySnapshot);
        }
        break;
      case "brain_snapshot":
        setBrain(payload as unknown as BrainSnapshot);
        pushActivity("Goal", String((payload as BrainSnapshot).snapshot.goal || ""));
        break;
      case "brain_graph":
        break;
      case "memory_snapshot":
        setMemory(payload as unknown as MemorySnapshot);
        break;
      case "voice":
        pushActivity(String(payload.name || "Voice"), String(payload.text || ""));
        break;
      case "belief":
        pushActivity("Belief", String(payload.text || ""));
        break;
      case "response_start": {
        const sessionsPayload = payload.sessions as ChatSession[] | undefined;
        if (sessionsPayload) {
          setSessions(sessionsPayload);
        }
        break;
      }
      case "response_token":
        patchSessionMessage(
          String(payload.session_id || ""),
          String(payload.messageId || ""),
          (message) => ({ ...message, text: message.text + String(payload.token || "") }),
        );
        break;
      case "response_end": {
        const sessionsPayload = payload.sessions as ChatSession[] | undefined;
        if (sessionsPayload) {
          setSessions(sessionsPayload);
        }
        break;
      }
      case "error":
        setStatus((prev) => ({ ...prev, lastError: String(payload.message || "Unknown error") }));
        pushActivity("Error", String(payload.message || "Unknown error"));
        break;
      case "process_exit":
        pushActivity("Process", `Exited (${payload.code ?? "?"})`);
        break;
      default:
        break;
    }
  }

  async function createSession() {
    const response = await fetch("/api/history/sessions", { method: "POST" });
    const data = await response.json();
    setSessions(data.sessions || []);
    setCurrentSessionId(data.session.id);
  }

  async function deleteSession(sessionId: string) {
    const response = await fetch(`/api/history/sessions/${sessionId}`, { method: "DELETE" });
    const data = await response.json();
    setSessions(data.sessions || []);
    if (sessionId === currentSessionId) {
      setCurrentSessionId(data.sessions?.[0]?.id || "");
    }
  }

  async function switchModel() {
    if (!selectedModel) {
      return;
    }

    setSwitchingModel(true);
    setComposerDisabled(true);
    pushActivity("Model", `Switching to ${selectedModel}`);

    const response = await fetch("/api/model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: selectedModel }),
    });

    if (!response.ok) {
      const data = await response.json();
      setSwitchingModel(false);
      setComposerDisabled(false);
      pushActivity("Error", data.error || "Failed to switch model");
    }
  }

  function sendMessage() {
    const text = input.trim();
    if (!text || !currentSessionId || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(JSON.stringify({ type: "user_message", text, sessionId: currentSessionId }));
    setInput("");
  }

  const stateVectorEntries = Object.entries(brain?.snapshot.state_vector || {});

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand-card">
          <div className="brand-mark">A</div>
          <div>
            <p className="eyebrow">Autonomous Reflective Intelligence</p>
            <h1>ARI Console</h1>
          </div>
        </div>

        <button className="new-chat-button" onClick={createSession} type="button">
          New chat
        </button>

        <section className="panel history-panel">
          <div className="panel-header">
            <span>History</span>
            <span>{sessions.length}</span>
          </div>
          <div className="history-list">
            {sortedSessions.map((session) => (
              <div key={session.id} className={`history-item ${session.id === currentSessionId ? "active" : ""}`}>
                <button className="history-select" onClick={() => setCurrentSessionId(session.id)} type="button">
                  <strong>{session.title}</strong>
                  <small>{new Date(session.updatedAt).toLocaleString()}</small>
                </button>
                <button className="history-remove" onClick={() => deleteSession(session.id)} type="button">
                  x
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <span>Runtime</span>
            <span className={`status-pill status-${status.state}`}>{connectionLabel}</span>
          </div>

          <label className="field-label" htmlFor="model-select">Model</label>
          <select
            id="model-select"
            className="input-control"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={loadingModels || switchingModel}
          >
            {models.map((model) => (
              <option key={model.name} value={model.name}>
                {model.name}
              </option>
            ))}
          </select>

          <button className="primary-button" onClick={switchModel} disabled={switchingModel || !selectedModel}>
            {switchingModel ? "Restarting..." : "Switch model"}
          </button>

          <dl className="stats-grid">
            <div>
              <dt>Current</dt>
              <dd>{status.model}</dd>
            </div>
            <div>
              <dt>Tick</dt>
              <dd>{status.lastTick}</dd>
            </div>
          </dl>

          {status.lastError ? <p className="error-text">{status.lastError}</p> : null}
        </section>

        <section className="panel models-panel">
          <div className="panel-header">
            <span>Available models</span>
            <span>{models.length}</span>
          </div>
          <div className="model-list">
            {models.map((model) => (
              <button
                key={model.name}
                className={`model-chip ${selectedModel === model.name ? "active" : ""}`}
                onClick={() => setSelectedModel(model.name)}
                type="button"
              >
                <span>{model.name}</span>
                <small>{formatBytes(model.size)}</small>
              </button>
            ))}
          </div>
        </section>
      </aside>

      <main className="chat-column">
        <header className="chat-header">
          <div>
            <p className="eyebrow">Conversation</p>
            <h2>{currentSession?.title || "Speak with ARI"}</h2>
          </div>
          <div className="header-meta">
            <span>{status.model}</span>
            <span>{connectionLabel}</span>
          </div>
        </header>

        <div className="messages">
          {messages.length === 0 ? (
            <div className="empty-state">
              <h3>ARI is ready.</h3>
              <p>Messages stream in real time from Python through Node. Select a chat from history or start a new one.</p>
            </div>
          ) : null}

          {messages.map((message) => (
            <article key={message.id} className={`message-card ${message.role}`}>
              <p className="message-title">{message.title}</p>
              <p>{message.text}</p>
            </article>
          ))}
          <div ref={bottomRef} />
        </div>

        <footer className="composer-shell">
          <div className="composer">
            <textarea
              className="composer-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Напиши повідомлення для ARI..."
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              disabled={composerDisabled}
            />
            <button className="send-button" onClick={sendMessage} disabled={composerDisabled || !input.trim()}>
              Send
            </button>
          </div>
        </footer>
      </main>

      <aside className="activity-column">
        <BrainGraph />

        <section className="panel status-panel sticky-card">
          <div className="panel-header">
            <span>ARI state</span>
            <span className={`status-pill status-${status.state}`}>{status.state}</span>
          </div>
          <dl className="stats-grid wide">
            <div>
              <dt>Current goal</dt>
              <dd>{brain?.snapshot.goal || "Awaiting first tick"}</dd>
            </div>
            <div>
              <dt>Current state</dt>
              <dd>{brain?.snapshot.state || "No synthesis yet"}</dd>
            </div>
          </dl>
          <div className="vector-list">
            {stateVectorEntries.map(([name, value]) => (
              <div key={name} className="vector-row">
                <div className="vector-meta">
                  <span>{name}</span>
                  <span>{Math.round(value * 100)}%</span>
                </div>
                <div className="vector-bar"><span style={{ width: `${Math.round(value * 100)}%` }} /></div>
              </div>
            ))}
          </div>
          <div className="status-block">
            <p className="activity-label">Beliefs</p>
            <div className="belief-list">
              {(brain?.snapshot.beliefs || []).map((belief) => (
                <p key={belief} className="activity-detail">{belief}</p>
              ))}
            </div>
          </div>
        </section>

        <section className="panel voice-panel">
          <div className="panel-header">
            <span>Voice outputs</span>
            <span>{voiceCards.length}</span>
          </div>
          <div className="activity-list compact">
            {voiceCards.map(([name, text]) => (
              <article key={name} className="activity-card">
                <p className="activity-label">{name}</p>
                <p className="activity-detail">{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="panel memory-panel">
          <div className="panel-header">
            <span>Memory viewer</span>
            <span>{memory?.total || 0}</span>
          </div>
          <div className="status-block">
            <p className="activity-label">Active query</p>
            <p className="activity-detail">{memory?.query || "No query yet"}</p>
          </div>
          <div className="memory-columns">
            <div>
              <p className="activity-label">Recalled</p>
              <div className="memory-list">
                {(memory?.recalled || []).map((item) => (
                  <article key={item.id} className="activity-card">
                    <p className="activity-label">{item.kind} · w={item.weight.toFixed(2)}</p>
                    <p className="activity-detail">{item.text}</p>
                  </article>
                ))}
              </div>
            </div>
            <div>
              <p className="activity-label">Recent</p>
              <div className="memory-list">
                {(memory?.recent || []).map((item) => (
                  <article key={item.id} className="activity-card">
                    <p className="activity-label">{item.kind} · w={item.weight.toFixed(2)}</p>
                    <p className="activity-detail">{item.text}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="panel feed-panel">
          <div className="panel-header">
            <span>Cognition feed</span>
            <span>{activity.length}</span>
          </div>
          <div className="activity-list">
            {activity.map((item) => (
              <article key={item.id} className="activity-card">
                <p className="activity-label">{item.label}</p>
                <p className="activity-detail">{item.detail}</p>
              </article>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}

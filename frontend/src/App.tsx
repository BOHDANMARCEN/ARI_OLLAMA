import { useEffect, useMemo, useRef, useState } from "react";

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

const initialStatus: BackendStatus = {
  type: "status_snapshot",
  model: "qwen3.5:9b",
  state: "connecting",
  lastError: null,
  lastTick: 0,
};

const STORAGE_KEY = "ari-ui-sessions";

function formatBytes(size?: number) {
  if (!size) {
    return "cloud";
  }

  const gb = size / (1024 ** 3);
  return `${gb.toFixed(1)} GB`;
}

export default function App() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState("");
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState("qwen3.5:9b");
  const [status, setStatus] = useState<BackendStatus>(initialStatus);
  const [input, setInput] = useState("");
  const [switchingModel, setSwitchingModel] = useState(false);
  const [loadingModels, setLoadingModels] = useState(true);
  const [composerDisabled, setComposerDisabled] = useState(false);
  const [currentGoal, setCurrentGoal] = useState("Awaiting first synthesis");
  const [latestBelief, setLatestBelief] = useState("No beliefs consolidated yet");
  const [voiceMap, setVoiceMap] = useState<Record<string, string>>({});

  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const streamTimersRef = useRef<number[]>([]);

  const currentSession = useMemo(
    () => sessions.find((session) => session.id === currentSessionId) ?? null,
    [sessions, currentSessionId],
  );

  const messages = currentSession?.messages ?? [];

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
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as ChatSession[];
        if (parsed.length > 0) {
          setSessions(parsed);
          setCurrentSessionId(parsed[0].id);
          return;
        }
      }
    } catch {
      // ignore corrupted local history
    }

    const starter = createSession();
    setSessions([starter]);
    setCurrentSessionId(starter.id);
  }, []);

  useEffect(() => {
    if (sessions.length > 0) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    }
  }, [sessions]);

  useEffect(() => {
    void loadModels();
    void loadStatus();
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);
    wsRef.current = socket;

    socket.onopen = () => {
      setStatus((prev) => ({ ...prev, state: prev.state === "connecting" ? "starting" : prev.state }));
    };

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      handleSocketEvent(payload);
    };

    socket.onclose = () => {
      setStatus((prev) => ({ ...prev, state: "stopped" }));
    };

    return () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      for (const timer of streamTimersRef.current) {
        window.clearTimeout(timer);
      }
      streamTimersRef.current = [];
    };
  }, []);

  function createSession(): ChatSession {
    const now = new Date().toISOString();
    return {
      id: crypto.randomUUID(),
      title: "New ARI chat",
      createdAt: now,
      updatedAt: now,
      messages: [],
    };
  }

  function patchCurrentSession(updater: (session: ChatSession) => ChatSession) {
    setSessions((prev) => prev.map((session) => (
      session.id === currentSessionId ? updater(session) : session
    )));
  }

  function startNewChat() {
    const session = createSession();
    setSessions((prev) => [session, ...prev]);
    setCurrentSessionId(session.id);
  }

  function removeSession(sessionId: string) {
    setSessions((prev) => {
      const next = prev.filter((session) => session.id !== sessionId);
      if (next.length === 0) {
        const fallback = createSession();
        setCurrentSessionId(fallback.id);
        return [fallback];
      }
      if (sessionId === currentSessionId) {
        setCurrentSessionId(next[0].id);
      }
      return next;
    });
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
    setSelectedModel(data.model || "qwen3.5:9b");
  }

  function pushActivity(label: string, detail: string) {
    setActivity((prev) => [{ id: crypto.randomUUID(), label, detail }, ...prev].slice(0, 14));
  }

  function streamAssistantMessage(text: string, tick: number | string | undefined) {
    const messageId = crypto.randomUUID();

    patchCurrentSession((session) => ({
      ...session,
      updatedAt: new Date().toISOString(),
      messages: [
        ...session.messages,
        {
          id: messageId,
          role: "assistant",
          title: `ARI · Tick ${tick ?? "?"}`,
          text: "",
        },
      ],
    }));

    const chunks = text.match(/.{1,8}/g) ?? [text];
    const typeChunk = (index: number) => {
      patchCurrentSession((session) => ({
        ...session,
        updatedAt: new Date().toISOString(),
        messages: session.messages.map((message) => (
          message.id === messageId
            ? { ...message, text: chunks.slice(0, index + 1).join("") }
            : message
        )),
      }));

      if (index < chunks.length - 1) {
        const timer = window.setTimeout(() => typeChunk(index + 1), 18);
        streamTimersRef.current.push(timer);
      }
    };

    typeChunk(0);
  }

  function buildSessionTitle(text: string) {
    return text.trim().slice(0, 42) || "New ARI chat";
  }

  function handleSocketEvent(payload: BackendStatus & Record<string, unknown>) {
    switch (payload.type) {
      case "status_snapshot":
        setStatus(payload as BackendStatus);
        setSwitchingModel(false);
        setComposerDisabled(payload.state !== "running");
        pushActivity("System", `${payload.state} on ${payload.model}`);
        break;
      case "status":
        pushActivity("Lifecycle", `${payload.phase} (${String(payload.model)})`);
        break;
      case "tick_start":
        setStatus((prev) => ({ ...prev, lastTick: Number(payload.tick || prev.lastTick) }));
        pushActivity("Tick", `Tick #${payload.tick}`);
        break;
      case "goal_updated":
        setCurrentGoal(String(payload.goal || ""));
        pushActivity("Goal", String(payload.goal || ""));
        break;
      case "voice":
        setVoiceMap((prev) => ({ ...prev, [String(payload.name || "Voice")]: String(payload.text || "") }));
        pushActivity(String(payload.name || "Voice"), String(payload.text || ""));
        break;
      case "belief":
        setLatestBelief(String(payload.text || ""));
        pushActivity("Belief", String(payload.text || ""));
        break;
      case "response":
        streamAssistantMessage(
          String(payload.text || ""),
          typeof payload.tick === "number" || typeof payload.tick === "string" ? payload.tick : undefined,
        );
        break;
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
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !currentSessionId) {
      return;
    }

    wsRef.current.send(JSON.stringify({ type: "user_message", text }));
    patchCurrentSession((session) => ({
      ...session,
      title: session.messages.length === 0 ? buildSessionTitle(text) : session.title,
      updatedAt: new Date().toISOString(),
      messages: [
        ...session.messages,
        {
          id: crypto.randomUUID(),
          role: "user",
          title: "You",
          text,
        },
      ],
    }));
    setInput("");
  }

  const sortedSessions = useMemo(
    () => [...sessions].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)),
    [sessions],
  );

  const voiceCards = useMemo(
    () => Object.entries(voiceMap).map(([name, text]) => ({ name, text })),
    [voiceMap],
  );

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

        <button className="new-chat-button" onClick={startNewChat} type="button">
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
                <button
                  className="history-remove"
                  onClick={() => removeSession(session.id)}
                  type="button"
                  aria-label="Delete chat"
                >
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
              <p>Start a new conversation or continue one from history. ARI will inject your message into the current cognition loop.</p>
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
        <section className="panel status-panel sticky-card">
          <div className="panel-header">
            <span>ARI state</span>
            <span className={`status-pill status-${status.state}`}>{status.state}</span>
          </div>
          <dl className="stats-grid wide">
            <div>
              <dt>Model</dt>
              <dd>{status.model}</dd>
            </div>
            <div>
              <dt>Last tick</dt>
              <dd>{status.lastTick}</dd>
            </div>
          </dl>
          <div className="status-block">
            <p className="activity-label">Current goal</p>
            <p className="activity-detail">{currentGoal}</p>
          </div>
          <div className="status-block">
            <p className="activity-label">Latest belief</p>
            <p className="activity-detail">{latestBelief}</p>
          </div>
        </section>

        <section className="panel voice-panel">
          <div className="panel-header">
            <span>Voice outputs</span>
            <span>{voiceCards.length}</span>
          </div>
          <div className="activity-list compact">
            {voiceCards.map((voice) => (
              <article key={voice.name} className="activity-card">
                <p className="activity-label">{voice.name}</p>
                <p className="activity-detail">{voice.text}</p>
              </article>
            ))}
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

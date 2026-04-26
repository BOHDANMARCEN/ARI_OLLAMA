import express from "express";
import { createServer } from "http";
import { spawn } from "child_process";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { WebSocketServer } from "ws";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");
const FRONTEND_DIST = path.join(ROOT_DIR, "frontend", "dist");
const ARI_SERVICE = path.join(ROOT_DIR, "ari_service.py");
const DATA_DIR = path.join(__dirname, "data");
const HISTORY_PATH = path.join(DATA_DIR, "chat-history.json");
const PYTHON_EXECUTABLE = process.platform === "win32"
  ? path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
  : path.join(ROOT_DIR, ".venv", "bin", "python");

const app = express();
const server = createServer(app);
const wss = new WebSocketServer({ server, path: "/ws" });

app.use(express.json());

let currentModel = process.env.ARI_MODEL || "qwen3.5:9b";
let ariProcess = null;
let ariStdoutBuffer = "";
let processState = "stopped";
let lastError = null;
let lastTick = 0;
let restartPromise = Promise.resolve();
let history = { sessions: [] };
let latestBrainSnapshot = null;
let latestMemorySnapshot = null;
let latestBrainGraph = null;
const pendingAssistantMessages = new Map();

function nowIso() {
  return new Date().toISOString();
}

function createSession(title = "New ARI chat") {
  const now = nowIso();
  return {
    id: crypto.randomUUID(),
    title,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

async function ensureDataDir() {
  await fs.mkdir(DATA_DIR, { recursive: true });
}

async function loadHistory() {
  await ensureDataDir();
  try {
    const raw = await fs.readFile(HISTORY_PATH, "utf8");
    history = JSON.parse(raw);
    if (!Array.isArray(history.sessions)) {
      history = { sessions: [] };
    }
  } catch {
    history = { sessions: [] };
  }
}

async function saveHistory() {
  await ensureDataDir();
  await fs.writeFile(HISTORY_PATH, JSON.stringify(history, null, 2), "utf8");
}

function getSessions() {
  return [...history.sessions].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

function findSession(sessionId) {
  return history.sessions.find((session) => session.id === sessionId) ?? null;
}

async function createStoredSession(title = "New ARI chat") {
  const session = createSession(title);
  history.sessions.unshift(session);
  await saveHistory();
  return session;
}

async function deleteStoredSession(sessionId) {
  history.sessions = history.sessions.filter((session) => session.id !== sessionId);
  await saveHistory();
}

async function appendMessage(sessionId, message) {
  const session = findSession(sessionId);
  if (!session) {
    throw new Error("Unknown session");
  }
  session.messages.push(message);
  session.updatedAt = nowIso();
  if (session.messages.length === 1 && message.role === "user") {
    session.title = message.text.slice(0, 42) || session.title;
  }
  await saveHistory();
  return session;
}

async function updateMessageText(sessionId, messageId, token) {
  const session = findSession(sessionId);
  if (!session) {
    return;
  }
  const message = session.messages.find((item) => item.id === messageId);
  if (!message) {
    return;
  }
  message.text += token;
  session.updatedAt = nowIso();
  await saveHistory();
}

function broadcast(event) {
  const payload = JSON.stringify(event);
  for (const client of wss.clients) {
    if (client.readyState === 1) {
      client.send(payload);
    }
  }
}

function snapshotEvent() {
  return {
    type: "status_snapshot",
    model: currentModel,
    state: processState,
    lastError,
    lastTick,
  };
}

function dashboardSnapshot() {
  return {
    type: "dashboard_snapshot",
    status: snapshotEvent(),
    brain: latestBrainSnapshot,
    memory: latestMemorySnapshot,
    brain_graph: latestBrainGraph,
  };
}

function handleAriLine(line) {
  if (!line.trim()) {
    return;
  }

  try {
    const event = JSON.parse(line);
    if (event.type === "tick_start") {
      lastTick = event.tick;
    }
    if (event.type === "error") {
      lastError = event.message;
    }
    if (event.type === "brain_snapshot") {
      latestBrainSnapshot = event;
    }
    if (event.type === "memory_snapshot") {
      latestMemorySnapshot = event;
    }
    if (event.type === "brain_graph") {
      latestBrainGraph = event.graph;
    }
    handleServiceEvent(event).catch((error) => {
      broadcast({ type: "error", message: error.message });
    });
  } catch {
    broadcast({ type: "log", channel: "stdout", text: line });
  }
}

async function handleServiceEvent(event) {
  if (event.type === "response_start") {
    const session = findSession(event.session_id);
    if (!session) {
      return;
    }
    const messageId = crypto.randomUUID();
    pendingAssistantMessages.set(event.session_id, messageId);
    await appendMessage(event.session_id, {
      id: messageId,
      role: "assistant",
      title: `ARI · Tick ${event.tick ?? "?"}`,
      text: "",
      createdAt: nowIso(),
    });
    broadcast({ ...event, messageId, sessions: getSessions() });
    return;
  }

  if (event.type === "response_token") {
    const messageId = pendingAssistantMessages.get(event.session_id);
    if (!messageId) {
      return;
    }
    await updateMessageText(event.session_id, messageId, event.token || "");
    broadcast({ ...event, messageId });
    return;
  }

  if (event.type === "response_end") {
    const messageId = pendingAssistantMessages.get(event.session_id);
    pendingAssistantMessages.delete(event.session_id);
    broadcast({ ...event, messageId, sessions: getSessions() });
    return;
  }

  if (event.type === "message_received" || event.type === "response") {
    return;
  }

  broadcast(event);
}

function wireProcessStreams(child) {
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");

  child.stdout.on("data", (chunk) => {
    ariStdoutBuffer += chunk;
    const lines = ariStdoutBuffer.split(/\r?\n/);
    ariStdoutBuffer = lines.pop() ?? "";
    for (const line of lines) {
      handleAriLine(line);
    }
  });

  child.stderr.on("data", (chunk) => {
    const text = chunk.toString();
    lastError = text.trim() || lastError;
    broadcast({ type: "log", channel: "stderr", text });
  });

  child.on("close", (code, signal) => {
    processState = "stopped";
    broadcast({ type: "process_exit", code, signal, model: currentModel });
    broadcast(snapshotEvent());
  });
}

async function startAri() {
  processState = "starting";
  lastError = null;
  broadcast(snapshotEvent());

  ariProcess = spawn(PYTHON_EXECUTABLE, [ARI_SERVICE], {
    cwd: ROOT_DIR,
    env: {
      ...process.env,
      PYTHONIOENCODING: "utf-8",
      ARI_MODEL: currentModel,
      ARI_THINK: process.env.ARI_THINK || "0",
    },
    stdio: ["pipe", "pipe", "pipe"],
  });

  ariStdoutBuffer = "";
  wireProcessStreams(ariProcess);
  processState = "running";
  broadcast(snapshotEvent());
}

async function stopAri() {
  if (!ariProcess) {
    processState = "stopped";
    return;
  }

  const child = ariProcess;
  ariProcess = null;
  processState = "stopping";
  broadcast(snapshotEvent());

  const exitPromise = new Promise((resolve) => {
    child.once("close", resolve);
  });

  try {
    child.stdin.write(JSON.stringify({ type: "shutdown" }) + "\n");
  } catch {
    child.kill();
  }

  const timeoutPromise = new Promise((resolve) => {
    setTimeout(() => {
      if (!child.killed) {
        child.kill();
      }
      resolve();
    }, 5000);
  });

  await Promise.race([exitPromise, timeoutPromise]);
  processState = "stopped";
  broadcast(snapshotEvent());
}

function queueRestart(nextModel) {
  restartPromise = restartPromise.then(async () => {
    if (nextModel) {
      currentModel = nextModel;
    }
    await stopAri();
    await startAri();
  });

  return restartPromise;
}

function sendToAri(payload) {
  if (!ariProcess || processState !== "running") {
    throw new Error("ARI process is not ready");
  }
  ariProcess.stdin.write(JSON.stringify(payload) + "\n");
}

app.get("/api/models", async (_req, res) => {
  try {
    const response = await fetch("http://127.0.0.1:11434/api/tags");
    if (!response.ok) {
      throw new Error(`Ollama returned ${response.status}`);
    }

    const data = await response.json();
    res.json({ currentModel, models: data.models || [] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get("/api/status", (_req, res) => {
  res.json(snapshotEvent());
});

app.get("/api/history", (_req, res) => {
  res.json({ sessions: getSessions() });
});

app.post("/api/history/sessions", async (req, res) => {
  const session = await createStoredSession(req.body?.title || "New ARI chat");
  broadcast({ type: "history_snapshot", sessions: getSessions() });
  res.json({ session, sessions: getSessions() });
});

app.delete("/api/history/sessions/:sessionId", async (req, res) => {
  await deleteStoredSession(req.params.sessionId);
  if (history.sessions.length === 0) {
    await createStoredSession();
  }
  broadcast({ type: "history_snapshot", sessions: getSessions() });
  res.json({ ok: true, sessions: getSessions() });
});

app.get("/api/dashboard", (_req, res) => {
  res.json(dashboardSnapshot());
});

app.post("/api/model", async (req, res) => {
  const model = req.body?.model;
  if (!model || typeof model !== "string") {
    res.status(400).json({ error: "Model is required" });
    return;
  }

  try {
    await queueRestart(model);
    res.json({ ok: true, model: currentModel });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post("/api/message", async (req, res) => {
  const text = req.body?.text;
  const sessionId = req.body?.sessionId;
  if (!text || typeof text !== "string") {
    res.status(400).json({ error: "Text is required" });
    return;
  }
  if (!sessionId || typeof sessionId !== "string") {
    res.status(400).json({ error: "sessionId is required" });
    return;
  }

  try {
    await appendMessage(sessionId, {
      id: crypto.randomUUID(),
      role: "user",
      title: "You",
      text,
      createdAt: nowIso(),
    });
    broadcast({ type: "history_snapshot", sessions: getSessions() });
    sendToAri({ type: "user_message", text, session_id: sessionId });
    res.json({ ok: true, sessions: getSessions() });
  } catch (error) {
    res.status(503).json({ error: error.message });
  }
});

app.use(express.static(FRONTEND_DIST));
app.get(/^(?!\/api).*/, (_req, res) => {
  res.sendFile(path.join(FRONTEND_DIST, "index.html"));
});

wss.on("connection", (socket) => {
  socket.send(JSON.stringify(snapshotEvent()));
  socket.send(JSON.stringify({ type: "history_snapshot", sessions: getSessions() }));
  socket.send(JSON.stringify(dashboardSnapshot()));

  socket.on("message", async (raw) => {
    try {
      const message = JSON.parse(raw.toString());
      if (message.type === "user_message") {
        const sessionId = message.sessionId;
        if (!sessionId) {
          throw new Error("sessionId is required");
        }
        await appendMessage(sessionId, {
          id: crypto.randomUUID(),
          role: "user",
          title: "You",
          text: message.text || "",
          createdAt: nowIso(),
        });
        broadcast({ type: "history_snapshot", sessions: getSessions() });
        sendToAri({ type: "user_message", text: message.text || "", session_id: sessionId });
      }
    } catch (error) {
      socket.send(JSON.stringify({ type: "error", message: error.message }));
    }
  });
});

const port = Number(process.env.PORT || 3000);
server.listen(port, async () => {
  await loadHistory();
  if (history.sessions.length === 0) {
    await createStoredSession();
  }
  await startAri();
  console.log(`ARI server listening on http://localhost:${port}`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, async () => {
    await stopAri();
    process.exit(0);
  });
}

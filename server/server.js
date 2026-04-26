import express from "express";
import { createServer } from "http";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import { WebSocketServer } from "ws";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, "..");
const FRONTEND_DIST = path.join(ROOT_DIR, "frontend", "dist");
const ARI_SERVICE = path.join(ROOT_DIR, "ari_service.py");
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
    broadcast(event);
  } catch {
    broadcast({ type: "log", channel: "stdout", text: line });
  }
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

app.post("/api/message", (req, res) => {
  const text = req.body?.text;
  if (!text || typeof text !== "string") {
    res.status(400).json({ error: "Text is required" });
    return;
  }

  try {
    sendToAri({ type: "user_message", text });
    res.json({ ok: true });
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

  socket.on("message", (raw) => {
    try {
      const message = JSON.parse(raw.toString());
      if (message.type === "user_message") {
        sendToAri({ type: "user_message", text: message.text || "" });
      }
    } catch (error) {
      socket.send(JSON.stringify({ type: "error", message: error.message }));
    }
  });
});

const port = Number(process.env.PORT || 3000);
server.listen(port, async () => {
  await startAri();
  console.log(`ARI server listening on http://localhost:${port}`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, async () => {
    await stopAri();
    process.exit(0);
  });
}

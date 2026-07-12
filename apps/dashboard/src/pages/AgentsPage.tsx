import { useEffect, useState } from "react";
import { fetchHealth, sendChat } from "../api";
import { useStore } from "../store";
import type { LogEntry } from "../store";

interface Agent {
  id: string;
  name: string;
  status: "online" | "offline" | "busy";
  lastSeen: string;
}

// Mock agents for display — replace with real API when available
const MOCK_AGENTS: Agent[] = [
  { id: "agent-001", name: "Sensor Monitor", status: "online", lastSeen: new Date().toISOString() },
  { id: "agent-002", name: "Payment Processor", status: "online", lastSeen: new Date().toISOString() },
  { id: "agent-003", name: "Data Aggregator", status: "busy", lastSeen: new Date().toISOString() },
];

const STATUS_COLORS: Record<string, string> = {
  online: "bg-hud-success",
  offline: "bg-hud-muted",
  busy: "bg-hud-warning pulse-dot",
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>(MOCK_AGENTS);
  const [chatInput, setChatInput] = useState("");
  const [chatBusy, setChatBusy] = useState(false);
  const logs = useStore((s) => s.logs);
  const addLog = useStore((s) => s.addLog);

  useEffect(() => {
    // Verify backend is reachable
    fetchHealth().catch(() => {});
  }, []);

  const a2aLogs = logs.filter(
    (l) => l.source === "a2a" || l.source === "agent" || l.source === "ws",
  );

  const handleSendChat = async () => {
    const msg = chatInput.trim();
    if (!msg) return;
    setChatBusy(true);
    addLog({
      timestamp: new Date().toISOString(),
      level: "info",
      source: "user",
      message: msg,
    });
    try {
      const res = await sendChat(msg);
      addLog({
        timestamp: new Date().toISOString(),
        level: "info",
        source: "agent",
        message: res.reply ?? JSON.stringify(res),
      });
    } catch (err) {
      addLog({
        timestamp: new Date().toISOString(),
        level: "error",
        source: "system",
        message: `Chat failed: ${err}`,
      });
    } finally {
      setChatBusy(false);
      setChatInput("");
    }
  };

  return (
    <div className="space-y-6">
      {/* Agent Grid */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-3">
          Registered Agents
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-[#12122a] rounded-md px-4 py-3 border border-[#2a2a4a] hover:border-hud-accent/30 transition-colors"
            >
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`inline-block w-2 h-2 rounded-full ${STATUS_COLORS[agent.status]}`}
                />
                <span className="font-mono text-sm text-hud-text">
                  {agent.name}
                </span>
              </div>
              <div className="text-xs text-hud-muted font-mono">{agent.id}</div>
              <div className="text-xs text-hud-muted mt-1">
                Last seen: {new Date(agent.lastSeen).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat / A2A Send */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-3">
          Send A2A Message
        </h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
            placeholder="Type a message to agents..."
            className="flex-1 bg-[#12122a] border border-[#2a2a4a] rounded-md px-3 py-2 text-sm text-hud-text placeholder:text-hud-muted focus:outline-none focus:border-hud-accent/50 font-mono"
          />
          <button
            onClick={handleSendChat}
            disabled={chatBusy}
            className="hud-btn disabled:opacity-50"
          >
            {chatBusy ? "Sending..." : "Send"}
          </button>
        </div>
      </div>

      {/* A2A Communication Log */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-3">
          A2A Communication Log
        </h3>
        <div className="max-h-80 overflow-auto space-y-1">
          {a2aLogs.length > 0 ? (
            a2aLogs.map((entry: LogEntry) => (
              <LogRow key={entry.id} entry={entry} />
            ))
          ) : (
            <p className="text-hud-muted text-sm">
              No A2A messages yet. Send a message above or wait for WebSocket events.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function LogRow({ entry }: { entry: LogEntry }) {
  const levelColor =
    entry.level === "error"
      ? "text-hud-danger"
      : entry.level === "warn"
        ? "text-hud-warning"
        : entry.level === "debug"
          ? "text-hud-muted"
          : "text-hud-accent";

  return (
    <div className="flex items-start gap-3 py-1 text-xs font-mono">
      <span className="text-hud-muted whitespace-nowrap">
        {new Date(entry.timestamp).toLocaleTimeString()}
      </span>
      <span className={`${levelColor} w-12 text-center uppercase`}>
        [{entry.source}]
      </span>
      <span className="text-hud-text break-all">{entry.message}</span>
    </div>
  );
}
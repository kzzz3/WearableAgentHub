import { useState } from "react";
import { useStore, type LogEntry } from "../store";

type LevelFilter = "all" | "info" | "warn" | "error" | "debug";

export default function LogsPage() {
  const logs = useStore((s) => s.logs);
  const clearLogs = useStore((s) => s.clearLogs);
  const [filter, setFilter] = useState<LevelFilter>("all");
  const [search, setSearch] = useState("");

  const filtered = logs.filter((l) => {
    if (filter !== "all" && l.level !== filter) return false;
    if (search && !l.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const LEVEL_STYLES: Record<string, string> = {
    info: "bg-hud-accent/10 text-hud-accent",
    warn: "bg-hud-warning/10 text-hud-warning",
    error: "bg-hud-danger/10 text-hud-danger",
    debug: "bg-[#2a2a4a] text-hud-muted",
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
          {(["all", "info", "warn", "error", "debug"] as LevelFilter[]).map(
            (level) => (
              <button
                key={level}
                onClick={() => setFilter(level)}
                className={`px-3 py-1.5 rounded text-xs font-mono uppercase transition-colors ${
                  filter === level
                    ? "bg-hud-accent/20 text-hud-accent border border-hud-accent/30"
                    : "bg-[#1a1a2e] text-hud-muted border border-[#2a2a4a] hover:text-hud-text"
                }`}
              >
                {level}
              </button>
            ),
          )}
        </div>

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search logs..."
          className="bg-[#12122a] border border-[#2a2a4a] rounded-md px-3 py-1.5 text-xs text-hud-text placeholder:text-hud-muted focus:outline-none focus:border-hud-accent/50 font-mono w-60"
        />

        <div className="flex-1" />

        <span className="text-xs text-hud-muted font-mono">
          {filtered.length} / {logs.length} entries
        </span>

        <button onClick={clearLogs} className="hud-btn-danger text-xs">
          Clear
        </button>
      </div>

      {/* Log Entries */}
      <div className="hud-card">
        <div className="max-h-[600px] overflow-auto space-y-px">
          {filtered.length > 0 ? (
            filtered.map((entry: LogEntry) => (
              <LogLine key={entry.id} entry={entry} levelStyles={LEVEL_STYLES} />
            ))
          ) : (
            <div className="flex items-center justify-center h-40 text-hud-muted text-sm">
              {logs.length === 0
                ? "No events recorded yet. Connect to the backend to see real-time logs."
                : "No logs match the current filter."}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LogLine({
  entry,
  levelStyles,
}: {
  entry: LogEntry;
  levelStyles: Record<string, string>;
}) {
  return (
    <div className="flex items-start gap-3 py-1.5 px-2 rounded hover:bg-[#1e1e36] transition-colors text-xs font-mono">
      <span className="text-hud-muted whitespace-nowrap min-w-[80px]">
        {new Date(entry.timestamp).toLocaleTimeString()}
      </span>
      <span
        className={`px-1.5 py-0.5 rounded text-[10px] uppercase min-w-[40px] text-center ${
          levelStyles[entry.level] ?? ""
        }`}
      >
        {entry.level}
      </span>
      <span className="text-hud-muted min-w-[60px]">[{entry.source}]</span>
      <span className="text-hud-text break-all flex-1">{entry.message}</span>
    </div>
  );
}
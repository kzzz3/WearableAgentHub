import { useEffect } from "react";
import { useStore, type ConnectionStatus } from "../store";

const STATUS_CONFIG: Record<ConnectionStatus, { color: string; label: string; dotClass: string }> = {
  connected: {
    color: "text-hud-success",
    label: "Connected",
    dotClass: "bg-hud-success",
  },
  disconnected: {
    color: "text-hud-muted",
    label: "Disconnected",
    dotClass: "bg-hud-muted",
  },
  processing: {
    color: "text-hud-warning",
    label: "Processing",
    dotClass: "bg-hud-warning pulse-dot",
  },
  error: {
    color: "text-hud-danger",
    label: "Error",
    dotClass: "bg-hud-danger pulse-dot",
  },
};

export default function StatusBadge() {
  const status = useStore((s) => s.connectionStatus);
  const connectWs = useStore((s) => s.connectWs);
  const cfg = STATUS_CONFIG[status];

  useEffect(() => {
    connectWs();
  }, [connectWs]);

  return (
    <div className="flex items-center gap-2">
      <span className={`inline-block w-2 h-2 rounded-full ${cfg.dotClass}`} />
      <span className={`text-xs font-mono ${cfg.color}`}>{cfg.label}</span>
    </div>
  );
}
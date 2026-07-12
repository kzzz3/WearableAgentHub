import { create } from "zustand";

export type ConnectionStatus = "connected" | "disconnected" | "processing" | "error";

export interface LogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warn" | "error" | "debug";
  source: string;
  message: string;
}

interface DashboardState {
  connectionStatus: ConnectionStatus;
  setConnectionStatus: (s: ConnectionStatus) => void;

  logs: LogEntry[];
  addLog: (entry: Omit<LogEntry, "id">) => void;
  clearLogs: () => void;

  ws: WebSocket | null;
  connectWs: (sessionId?: string) => void;
  disconnectWs: () => void;
}

let wsRef: WebSocket | null = null;

export const useStore = create<DashboardState>((set, get) => ({
  connectionStatus: "disconnected",
  setConnectionStatus: (s) => set({ connectionStatus: s }),

  logs: [],
  addLog: (entry) =>
    set((state) => ({
      logs: [
        { ...entry, id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}` },
        ...state.logs,
      ].slice(0, 500), // keep last 500
    })),
  clearLogs: () => set({ logs: [] }),

  ws: null,
  connectWs: (sessionId = "dashboard") => {
    if (wsRef && wsRef.readyState <= WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;

    try {
      const socket = new WebSocket(wsUrl);
      wsRef = socket;

      socket.onopen = () => {
        set({ connectionStatus: "connected", ws: socket });
        get().addLog({
          timestamp: new Date().toISOString(),
          level: "info",
          source: "ws",
          message: "WebSocket connected",
        });
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          get().addLog({
            timestamp: new Date().toISOString(),
            level: "info",
            source: data.source || "ws",
            message: typeof data === "string" ? data : JSON.stringify(data),
          });
        } catch {
          get().addLog({
            timestamp: new Date().toISOString(),
            level: "info",
            source: "ws",
            message: String(event.data),
          });
        }
      };

      socket.onclose = () => {
        set({ connectionStatus: "disconnected", ws: null });
        get().addLog({
          timestamp: new Date().toISOString(),
          level: "warn",
          source: "ws",
          message: "WebSocket disconnected",
        });
        wsRef = null;
      };

      socket.onerror = () => {
        set({ connectionStatus: "error" });
        get().addLog({
          timestamp: new Date().toISOString(),
          level: "error",
          source: "ws",
          message: "WebSocket error",
        });
      };
    } catch {
      set({ connectionStatus: "error" });
    }
  },

  disconnectWs: () => {
    if (wsRef) {
      wsRef.close();
      wsRef = null;
    }
    set({ ws: null, connectionStatus: "disconnected" });
  },
}));
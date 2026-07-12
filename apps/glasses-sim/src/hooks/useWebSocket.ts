import { useEffect, useRef, useCallback } from "react";
import { useHudStore } from "../store";

export function useWebSocket(sessionId: string = "default") {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { setConnected, addA2UIMessages, addHistory, setProcessing } = useHudStore();

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log("[WS] Connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "chat_response") {
          addHistory({ role: "assistant", text: data.reply || "" });
          if (data.a2ui_messages?.length) {
            addA2UIMessages(data.a2ui_messages);
          }
          setProcessing(false);
        } else if (data.type === "error") {
          addHistory({ role: "assistant", text: `[Error] ${data.message}` });
          setProcessing(false);
        }
      } catch (e) {
        console.error("[WS] Parse error:", e);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("[WS] Disconnected, reconnecting in 3s...");
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = (e) => console.error("[WS] Error:", e);
  }, [sessionId, setConnected, addA2UIMessages, addHistory, setProcessing]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: text, session_id: sessionId }));
      addHistory({ role: "user", text });
      setProcessing(true);
    }
  }, [sessionId, addHistory, setProcessing]);

  return { sendMessage };
}

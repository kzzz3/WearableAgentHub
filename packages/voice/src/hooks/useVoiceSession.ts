import { useEffect, useCallback, useRef, useState } from "react";
import type { VoiceMessage, VoiceState } from "../types";

interface UseVoiceSessionOptions {
  sessionId?: string;
  onTranscript?: (text: string) => void;
  onReply?: (text: string, source: string) => void;
  onA2UI?: (messages: unknown[]) => void;
  onPayment?: (receipt: unknown) => void;
  onStateChange?: (state: VoiceState) => void;
}

interface UseVoiceSessionReturn {
  state: VoiceState;
  isConnected: boolean;
  sendText: (text: string) => void;
  disconnect: () => void;
}

/**
 * Hook for connecting to the voice WebSocket endpoint.
 * Manages connection lifecycle, state transitions, and message routing.
 */
export function useVoiceSession(options: UseVoiceSessionOptions = {}): UseVoiceSessionReturn {
  const {
    sessionId = "default",
    onTranscript,
    onReply,
    onA2UI,
    onPayment,
    onStateChange,
  } = options;

  const [state, setState] = useState<VoiceState>("idle");
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Stable callback refs
  const callbacksRef = useRef({ onTranscript, onReply, onA2UI, onPayment, onStateChange });
  callbacksRef.current = { onTranscript, onReply, onA2UI, onPayment, onStateChange };

  const updateState = useCallback((newState: VoiceState) => {
    setState(newState);
    callbacksRef.current.onStateChange?.(newState);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const loc = window.location;
    const isViteDev = ["5173", "5174", "5175"].includes(loc.port);
    const protocol = loc.protocol === "https:" ? "wss:" : "ws:";
    const url = isViteDev
      ? `ws://localhost:8000/voice/${sessionId}`
      : `${protocol}//${loc.host}/voice/${sessionId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[Voice] Connected", url);
      setIsConnected(true);
      updateState("listening");
    };

    ws.onmessage = (event) => {
      try {
        const msg: VoiceMessage = JSON.parse(event.data);

        switch (msg.type) {
          case "transcript":
            if (msg.content) callbacksRef.current.onTranscript?.(msg.content);
            break;
          case "reply":
            if (msg.content) callbacksRef.current.onReply?.(msg.content, msg.source || "local");
            break;
          case "a2ui":
            if (msg.messages) callbacksRef.current.onA2UI?.(msg.messages);
            break;
          case "payment":
            if (msg.receipt) callbacksRef.current.onPayment?.(msg.receipt);
            break;
          case "status":
            if (msg.state) updateState(msg.state);
            break;
          case "error":
            console.error("[Voice] Server error:", msg.message);
            updateState("error");
            break;
        }
      } catch (err) {
        console.error("[Voice] Parse error:", err);
      }
    };

    ws.onclose = () => {
      console.log("[Voice] Disconnected, reconnecting in 2s...");
      setIsConnected(false);
      updateState("idle");
      reconnectRef.current = setTimeout(connect, 2000);
    };

    ws.onerror = (err) => {
      console.error("[Voice] WebSocket error:", err);
      updateState("error");
    };
  }, [sessionId, updateState]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectRef.current);
      if (wsRef.current) {
        wsRef.current.onopen = null;
        wsRef.current.onmessage = null;
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const sendText = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "text", content: text }));
      updateState("thinking");
    }
  }, [updateState]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectRef.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    updateState("idle");
  }, [updateState]);

  return { state, isConnected, sendText, disconnect };
}
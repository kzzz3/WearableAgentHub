import { useCallback } from "react";
import { useVoiceSession } from "@wearable-hub/voice";
import { useHudStore } from "../store";

export function VoiceButton() {
  const { addA2UIMessages, addHistory, setProcessing } = useHudStore();

  const onReply = useCallback(
    (text: string, source: string) => {
      addHistory({ role: "assistant", text, source: source as "local" | "a2a" });
      setProcessing(false);
    },
    [addHistory, setProcessing],
  );

  const onA2UI = useCallback(
    (messages: unknown[]) => {
      addA2UIMessages(messages as Parameters<typeof addA2UIMessages>[0]);
    },
    [addA2UIMessages],
  );

  const onTranscript = useCallback(
    (text: string) => {
      addHistory({ role: "user", text });
      setProcessing(true);
    },
    [addHistory, setProcessing],
  );

  const onStateChange = useCallback(
    (voiceState: string) => {
      if (voiceState === "thinking") setProcessing(true);
      if (voiceState === "listening") setProcessing(false);
    },
    [setProcessing],
  );

  const { state, isConnected, sendText } = useVoiceSession({
    sessionId: "default",
    onTranscript,
    onReply,
    onA2UI,
    onStateChange,
  });

  const isActive = state === "listening" || state === "thinking";

  return (
    <button
      onClick={() => {
        if (!isConnected) return;
        const test = prompt("Voice input (text simulation):");
        if (test?.trim()) sendText(test.trim());
      }}
      disabled={!isConnected}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono transition-all ${
        isConnected
          ? isActive
            ? "bg-green-500/20 border border-green-500/40 text-green-400 animate-pulse"
            : "bg-hud-accent/10 border border-hud-accent/30 text-hud-accent hover:bg-hud-accent/20"
          : "bg-hud-muted/10 border border-hud-muted/20 text-hud-muted cursor-not-allowed"
      }`}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
      </svg>
      {state === "thinking" ? "..." : "VOICE"}
    </button>
  );
}
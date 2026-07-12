import { A2UIRenderer } from "@wearable-hub/a2ui-renderer";
import { useHudStore } from "./store";
import { useWebSocket } from "./hooks/useWebSocket";
import { GlassesFrame } from "./components/GlassesFrame";
import { ChatInput } from "./components/ChatInput";
import { MessageBubble } from "./components/MessageBubble";

export default function App() {
  const { messages, history, isProcessing, connected } = useHudStore();
  const { sendMessage } = useWebSocket("default");

  return (
    <GlassesFrame>
      {history.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full gap-4 py-20">
          <div className="text-3xl font-mono text-hud-accent opacity-60">WearableAgent</div>
          <div className="text-sm text-hud-muted">Glasses HUD Simulator</div>
          <div className="flex gap-2 mt-4 flex-wrap justify-center">
            {["nearby cafes", "translate Hello World", "what time is it"].map((q) => (
              <button
                key={q}
                onClick={() => sendMessage(q)}
                className="text-xs px-3 py-1.5 border border-hud-accent/30 rounded-full text-hud-accent/70 hover:bg-hud-accent/10 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        {history.map((entry, i) => (
          <MessageBubble key={i} role={entry.role} text={entry.text} />
        ))}
        {messages.length > 0 && (
          <div className="mt-2">
            <A2UIRenderer messages={messages} />
          </div>
        )}
      </div>

      {isProcessing && (
        <div className="flex items-center gap-2 text-hud-accent animate-pulse mt-3">
          <div className="w-1.5 h-1.5 rounded-full bg-hud-accent" />
          <span className="text-xs font-mono">Processing...</span>
        </div>
      )}

      <ChatInput onSend={sendMessage} disabled={!connected || isProcessing} />
    </GlassesFrame>
  );
}

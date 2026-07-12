import { A2UIRenderer } from "@wearable-hub/a2ui-renderer";
import { useWatchStore } from "./store";
import { useWebSocket } from "./hooks/useWebSocket";
import { WatchFace } from "./components/WatchFace";
import { TimeDisplay } from "./components/TimeDisplay";
import { HealthWidget } from "./components/HealthWidget";
import { MiniMessage } from "./components/MiniMessage";
import { MiniInput } from "./components/MiniInput";

export default function App() {
  const { messages, history, isProcessing, connected } = useWatchStore();
  const { sendMessage } = useWebSocket("default");

  const hasContent = history.length > 0 || messages.length > 0;

  return (
    <WatchFace>
      {/* Top: Time */}
      <TimeDisplay />

      {/* Health widget below time */}
      <div className="mt-1">
        <HealthWidget />
      </div>

      {/* Divider */}
      <div className="w-full h-px bg-hud-accent/10 my-1" />

      {/* Center: Messages area */}
      <div className="flex-1 min-h-0 overflow-y-auto watch-scroll space-y-1.5 py-1">
        {!hasContent && (
          <div className="flex flex-col items-center justify-center h-full gap-2">
            <div className="text-[10px] font-mono text-hud-accent/60">WearableAgent</div>
            <div className="text-[8px] text-hud-muted">Watch Simulator</div>
            <div className="flex flex-col gap-1 mt-2 items-center">
              {["what time is it", "nearby cafes"].map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-[8px] px-2 py-0.5 border border-hud-accent/20 rounded-full text-hud-accent/60 hover:bg-hud-accent/10 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {hasContent && (
          <>
            {history.map((entry, i) => (
              <MiniMessage
                key={`hist-${i}-${entry.text.slice(0, 8)}`}
                role={entry.role}
                text={entry.text}
                source={entry.source}
                payment={entry.payment}
              />
            ))}
            {messages.length > 0 && (
              <div className="mt-1 [&_*]:!text-[8px] [&_*]:!leading-tight">
                <A2UIRenderer messages={messages} />
              </div>
            )}
          </>
        )}

        {isProcessing && (
          <div className="flex items-center gap-1.5 text-hud-accent animate-pulse">
            <div className="w-1 h-1 rounded-full bg-hud-accent" />
            <span className="text-[8px] font-mono">Thinking...</span>
          </div>
        )}
      </div>

      {/* Bottom: Input */}
      <div className="w-full">
        <div className="h-px bg-hud-accent/10 mb-1" />
        <div className="flex items-center justify-between px-1 mb-0.5">
          <div className="flex items-center gap-1">
            <div className={`w-1 h-1 rounded-full ${connected ? "bg-hud-success animate-pulse" : "bg-hud-danger"}`} />
            <span className="text-[7px] font-mono text-hud-muted">{connected ? "ONLINE" : "OFFLINE"}</span>
          </div>
          <span className="text-[7px] font-mono text-hud-accent/40">v0.1.0</span>
        </div>
        <MiniInput onSend={sendMessage} disabled={!connected || isProcessing} />
      </div>
    </WatchFace>
  );
}
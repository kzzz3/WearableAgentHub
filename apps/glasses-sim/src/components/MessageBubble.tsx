import type { PaymentReceipt } from "../store";
import { PaymentStatus } from "./payment/PaymentStatus";

interface MessageBubbleProps {
  role: "user" | "assistant";
  text: string;
  source?: "local" | "a2a";
  payment?: PaymentReceipt | null;
}

export function MessageBubble({ role, text, source, payment }: MessageBubbleProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}>
      <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
        role === "user"
          ? "bg-hud-accent/15 border border-hud-accent/30 text-hud-accent"
          : "bg-hud-card border border-hud-muted/20 text-hud-text"
      }`}>
        <span className="text-[10px] font-mono text-hud-muted block mb-1">
          {role === "user" ? "YOU" : "AGENT"}
          {source === "a2a" && (
            <span className="ml-1.5 inline-block px-1.5 py-0.5 text-[8px] bg-green-500/20 text-green-400 rounded border border-green-500/30">
              via A2A
            </span>
          )}
        </span>
        {text}
        {payment && (
          <div className="mt-2">
            <PaymentStatus payment={payment} />
          </div>
        )}
      </div>
    </div>
  );
}
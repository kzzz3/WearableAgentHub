import type { PaymentReceipt } from "../store";

interface MiniMessageProps {
  role: "user" | "assistant";
  text: string;
  source?: "local" | "a2a";
  payment?: PaymentReceipt | null;
}

function shortenAddress(addr: string): string {
  if (addr.length <= 10) return addr;
  return `${addr.slice(0, 5)}...${addr.slice(-3)}`;
}

function weiToEth(wei: string): string {
  const val = Number(wei) / 1e18;
  return val.toFixed(4);
}

export function MiniMessage({ role, text, source, payment }: MiniMessageProps) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}>
      <div
        className={`max-w-[85%] rounded-lg px-2 py-1 text-[9px] leading-tight ${
          role === "user"
            ? "bg-hud-accent/15 border border-hud-accent/30 text-hud-accent"
            : "bg-hud-card border border-hud-muted/20 text-hud-text"
        }`}
      >
        <span className="text-[7px] font-mono text-hud-muted block mb-0.5">
          {role === "user" ? "YOU" : "AGENT"}
          {source === "a2a" && (
            <span className="ml-1 inline-block px-1 py-0 text-[6px] bg-green-500/20 text-green-400 rounded border border-green-500/30">
              A2A
            </span>
          )}
        </span>
        <span className="line-clamp-2">{text}</span>
        {payment && (
          <div className="mt-1 pt-1 border-t border-green-500/20">
            <div className="flex items-center gap-1 mb-0.5">
              <span className="text-green-400 text-[7px]">●</span>
              <span className="text-green-400 text-[7px] font-bold">x402</span>
            </div>
            <div className="text-[7px] text-hud-muted space-y-0">
              <div>{payment.resource} · {weiToEth(payment.amount)} ETH</div>
              <div>{shortenAddress(payment.transactionId)}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
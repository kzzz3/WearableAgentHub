export function MessageBubble({ role, text }: { role: "user" | "assistant"; text: string }) {
  return (
    <div className={`flex ${role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}>
      <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
        role === "user"
          ? "bg-hud-accent/15 border border-hud-accent/30 text-hud-accent"
          : "bg-hud-card border border-hud-muted/20 text-hud-text"
      }`}>
        <span className="text-[10px] font-mono text-hud-muted block mb-1">
          {role === "user" ? "YOU" : "AGENT"}
        </span>
        {text}
      </div>
    </div>
  );
}

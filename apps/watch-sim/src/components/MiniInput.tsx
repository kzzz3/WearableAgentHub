import { useState, useRef } from "react";

export function MiniInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText("");
      inputRef.current?.focus();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-1 px-2 py-1">
      <input
        ref={inputRef}
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Ask..."
        disabled={disabled}
        className="flex-1 bg-hud-card/60 border border-hud-accent/20 rounded px-2 py-1 text-[9px] text-hud-text placeholder:text-hud-muted/50 focus:outline-none focus:border-hud-accent/50 font-mono min-w-0"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="px-2 py-1 bg-hud-accent/20 border border-hud-accent/40 rounded text-[9px] text-hud-accent hover:bg-hud-accent/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors font-mono"
      >
        {disabled ? "…" : "→"}
      </button>
    </form>
  );
}
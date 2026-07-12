import { useState, useRef, useEffect } from "react";

export function ChatInput({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [text, setText] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && !disabled) {
      onSend(text.trim());
      setText("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-3 border-t border-hud-accent/20 bg-hud-card/50">
      <input
        ref={inputRef}
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Say something..."
        disabled={disabled}
        className="flex-1 bg-transparent border border-hud-accent/30 rounded px-3 py-2 text-sm text-hud-text placeholder:text-hud-muted/50 focus:outline-none focus:border-hud-accent/60 font-mono"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="px-4 py-2 bg-hud-accent/20 border border-hud-accent/40 rounded text-sm text-hud-accent hover:bg-hud-accent/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors font-mono"
      >
        {disabled ? "..." : "SEND"}
      </button>
    </form>
  );
}

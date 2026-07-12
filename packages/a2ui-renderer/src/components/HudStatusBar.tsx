export function HudStatusBar({ items }: { items: Array<{ label: string; value: string; color?: string }> }) {
  return (
    <div className="flex gap-3 flex-wrap mt-2">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-1.5 text-xs">
          <span className={`w-1.5 h-1.5 rounded-full ${item.color || "bg-hud-accent"}`} />
          <span className="text-hud-muted">{item.label}:</span>
          <span className="text-hud-text font-mono">{item.value}</span>
        </div>
      ))}
    </div>
  );
}

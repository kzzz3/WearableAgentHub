export function HudList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1 mt-2">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-hud-text animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
          <span className="text-hud-accent text-xs mt-0.5">▸</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

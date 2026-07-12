export function HudText({ content, variant = "body" }: { content: string; variant?: "title" | "subtitle" | "body" | "caption" }) {
  const cls = {
    title: "text-lg font-bold text-hud-accent",
    subtitle: "text-sm text-hud-muted",
    body: "text-sm text-hud-text leading-relaxed",
    caption: "text-xs text-hud-muted",
  }[variant];
  return <p className={cls}>{content}</p>;
}

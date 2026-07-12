import { HudText } from "./HudText";

export function HudCard({ title, subtitle, children }: { title?: string; subtitle?: string; children?: React.ReactNode }) {
  return (
    <div className="bg-hud-card/80 backdrop-blur-sm border border-hud-accent/20 rounded-lg p-3 animate-slide-up">
      {title && <HudText content={title} variant="title" />}
      {subtitle && <HudText content={subtitle} variant="subtitle" />}
      {children}
    </div>
  );
}

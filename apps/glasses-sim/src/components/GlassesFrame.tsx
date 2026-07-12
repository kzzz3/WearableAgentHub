export function GlassesFrame({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="relative w-full max-w-2xl">
        <div className="flex items-center justify-between px-4 py-2 border-b border-hud-accent/20">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-hud-success animate-pulse" />
            <span className="text-xs font-mono text-hud-muted">HUD ACTIVE</span>
          </div>
          <span className="text-xs font-mono text-hud-muted">WearableAgent Hub</span>
          <span className="text-xs font-mono text-hud-accent">v0.1.0</span>
        </div>
        <div className="bg-hud-bg border-x border-hud-accent/10 min-h-[60vh] max-h-[70vh] overflow-y-auto p-4 scrollbar-thin">
          {children}
        </div>
        <div className="h-0.5 bg-gradient-to-r from-transparent via-hud-accent/40 to-transparent" />
      </div>
    </div>
  );
}

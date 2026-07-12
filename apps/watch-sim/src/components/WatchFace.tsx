export function WatchFace({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      {/* Outer bezel */}
      <div className="relative rounded-full bezel-gradient p-[6px] shadow-[0_0_40px_rgba(0,212,255,0.08)]">
        {/* Inner bezel ring */}
        <div className="rounded-full bg-watch-ring p-[3px]">
          {/* Side button indicator */}
          <div className="absolute right-[-4px] top-1/2 -translate-y-1/2 w-[6px] h-10 bg-watch-bezel rounded-r-sm border border-hud-muted/20" />

          {/* Watch surface (circular) */}
          <div className="relative w-[280px] h-[280px] rounded-full bg-watch-surface overflow-hidden flex flex-col">
            {/* Subtle inner shadow for depth */}
            <div className="absolute inset-0 rounded-full pointer-events-none shadow-[inset_0_0_30px_rgba(0,0,0,0.5)]" />

            {/* Content container - clips to circle */}
            <div className="relative flex-1 flex flex-col min-h-0 px-5 pt-5 pb-4">
              {children}
            </div>
          </div>
        </div>
      </div>

      {/* Brand label */}
      <div className="mt-4 text-[10px] text-hud-muted/40 font-mono tracking-widest text-center">
        WEARABLEAGENT HUB
      </div>
    </div>
  );
}
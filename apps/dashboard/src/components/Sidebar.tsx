import type { Page } from "../App";

interface SidebarProps {
  current: Page;
  onNavigate: (page: Page) => void;
}

const NAV_ITEMS: { page: Page; icon: string; label: string }[] = [
  { page: "overview", icon: "📊", label: "Overview" },
  { page: "agents", icon: "🤖", label: "Agents & A2A" },
  { page: "payments", icon: "💳", label: "Payments" },
  { page: "logs", icon: "📋", label: "Event Logs" },
  { page: "settings", icon: "⚙️", label: "Settings" },
];

export default function Sidebar({ current, onNavigate }: SidebarProps) {
  return (
    <aside className="w-56 flex-shrink-0 flex flex-col bg-hud-card border-r border-[#2a2a4a]">
      <div className="flex items-center gap-2 px-5 py-4 border-b border-[#2a2a4a]">
        <span className="text-xl">⚡</span>
        <span className="font-semibold text-hud-accent text-sm tracking-wider uppercase">
          WearableHub
        </span>
      </div>

      <nav className="flex-1 py-3">
        {NAV_ITEMS.map((item) => {
          const active = current === item.page;
          return (
            <button
              key={item.page}
              onClick={() => onNavigate(item.page)}
              className={`
                w-full flex items-center gap-3 px-5 py-2.5 text-sm text-left transition-all duration-150
                ${
                  active
                    ? "bg-hud-accent/10 text-hud-accent border-r-2 border-hud-accent"
                    : "text-hud-muted hover:text-hud-text hover:bg-[#22223a]"
                }
              `}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="px-5 py-4 border-t border-[#2a2a4a]">
        <div className="text-xs text-hud-muted font-mono">
          WearableAgentHub v0.1
        </div>
      </div>
    </aside>
  );
}
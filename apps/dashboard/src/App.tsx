import { useState } from "react";
import Sidebar from "./components/Sidebar";
import StatusBadge from "./components/StatusBadge";
import OverviewPage from "./pages/OverviewPage";
import PaymentsPage from "./pages/PaymentsPage";
import AgentsPage from "./pages/AgentsPage";
import LogsPage from "./pages/LogsPage";

export type Page = "overview" | "agents" | "payments" | "logs" | "settings";

export default function App() {
  const [page, setPage] = useState<Page>("overview");

  return (
    <div className="flex h-screen overflow-hidden bg-hud-bg">
      <Sidebar current={page} onNavigate={setPage} />
      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center justify-between px-6 py-3 border-b border-[#2a2a4a] bg-hud-bg/80 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <span className="text-lg font-semibold text-hud-text">
              {page === "overview" && "Overview"}
              {page === "agents" && "Agents & A2A"}
              {page === "payments" && "Payments"}
              {page === "logs" && "Event Logs"}
              {page === "settings" && "Settings"}
            </span>
          </div>
          <StatusBadge />
        </header>
        <main className="flex-1 overflow-auto p-6">
          {page === "overview" && <OverviewPage />}
          {page === "agents" && <AgentsPage />}
          {page === "payments" && <PaymentsPage />}
          {page === "logs" && <LogsPage />}
          {page === "settings" && <SettingsPlaceholder />}
        </main>
      </div>
    </div>
  );
}

function SettingsPlaceholder() {
  return (
    <div className="hud-card max-w-lg">
      <h2 className="text-lg font-semibold text-hud-text mb-2">Settings</h2>
      <p className="text-hud-muted text-sm">
        Configuration panel — coming soon. Backend URL, theme, and notification
        preferences will live here.
      </p>
    </div>
  );
}
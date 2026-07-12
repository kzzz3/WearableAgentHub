import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { fetchHealth, fetchServices, fetchPaymentHistory, fetchWallets } from "../api";
import { useStore } from "../store";
import type { Payment, Service, Wallet } from "../api";

export default function OverviewPage() {
  const [health, setHealth] = useState<string>("checking...");
  const [services, setServices] = useState<Service[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const status = useStore((s) => s.connectionStatus);

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth(h.status ?? "ok"))
      .catch(() => setHealth("unreachable"));

    fetchServices().then(setServices).catch(() => {});
    fetchPaymentHistory().then(setPayments).catch(() => {});
    fetchWallets().then(setWallets).catch(() => {});
  }, []);

  const totalPaid = payments.reduce((sum, p) => sum + (p.amount ?? 0), 0);
  const totalBalance = wallets.reduce((sum, w) => sum + (w.balance ?? 0), 0);

  // Build chart data: group payments by date
  const chartMap = new Map<string, number>();
  payments.forEach((p) => {
    const day = p.timestamp ? p.timestamp.slice(0, 10) : "unknown";
    chartMap.set(day, (chartMap.get(day) ?? 0) + (p.amount ?? 0));
  });
  const chartData = Array.from(chartMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, amount]) => ({ date, amount }));

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Backend Health"
          value={health}
          color={health === "ok" ? "text-hud-success" : "text-hud-danger"}
        />
        <MetricCard label="Services Available" value={String(services.length)} />
        <MetricCard label="Total Payments" value={String(payments.length)} />
        <MetricCard label="Total Spent" value={`${totalPaid.toFixed(2)}`} />
      </div>

      {/* Second row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Wallets" value={String(wallets.length)} />
        <MetricCard label="Total Balance" value={`${totalBalance.toFixed(2)}`} />
        <MetricCard
          label="WS Status"
          value={status}
          color={
            status === "connected"
              ? "text-hud-success"
              : status === "error"
                ? "text-hud-danger"
                : "text-hud-warning"
          }
        />
        <MetricCard label="Uptime" value="—" />
      </div>

      {/* Payment Volume Chart */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-4">
          Payment Volume
        </h3>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="gradAmount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" />
              <XAxis dataKey="date" tick={{ fill: "#8888aa", fontSize: 11 }} />
              <YAxis tick={{ fill: "#8888aa", fontSize: 11 }} />
              <Tooltip
                contentStyle={{
                  background: "#1a1a2e",
                  border: "1px solid #2a2a4a",
                  borderRadius: 8,
                  color: "#e0e0e0",
                  fontSize: 12,
                }}
              />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="#00d4ff"
                fillOpacity={1}
                fill="url(#gradAmount)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-40 text-hud-muted text-sm">
            No payment data yet
          </div>
        )}
      </div>

      {/* Recent Payments */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-3">
          Recent Payments
        </h3>
        {payments.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-hud-muted text-xs uppercase">
                  <th className="pb-2 pr-4">Service</th>
                  <th className="pb-2 pr-4">Payer</th>
                  <th className="pb-2 pr-4">Amount</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {payments.slice(0, 8).map((p, i) => (
                  <tr key={i} className="hud-table-row">
                    <td className="py-2 pr-4 font-mono text-hud-accent">{p.service}</td>
                    <td className="py-2 pr-4 font-mono text-hud-muted">{p.payer_wallet}</td>
                    <td className="py-2 pr-4">{p.amount ?? "—"}</td>
                    <td className="py-2 text-hud-muted text-xs">
                      {p.timestamp ? new Date(p.timestamp).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-hud-muted text-sm">No payments recorded yet.</p>
        )}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="hud-card">
      <div className="text-xs text-hud-muted uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className={`text-xl font-semibold font-mono ${color ?? "text-hud-text"}`}>
        {value}
      </div>
    </div>
  );
}
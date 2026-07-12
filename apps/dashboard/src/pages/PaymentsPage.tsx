import { useEffect, useState } from "react";
import {
  fetchPaymentHistory,
  fetchWallets,
  fetchServices,
  payService,
} from "../api";
import type { Payment, Wallet, Service } from "../api";

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [paying, setPaying] = useState<string | null>(null);

  const load = () => {
    fetchPaymentHistory().then(setPayments).catch(() => {});
    fetchWallets().then(setWallets).catch(() => {});
    fetchServices().then(setServices).catch(() => {});
  };

  useEffect(() => {
    load();
  }, []);

  const handlePay = async (serviceName: string) => {
    setPaying(serviceName);
    try {
      await payService(serviceName);
      load(); // refresh data
    } catch (err) {
      console.error("Payment failed:", err);
    } finally {
      setPaying(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Wallet Balances */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-3">
          Wallet Balances
        </h3>
        {wallets.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {wallets.map((w, i) => (
              <div
                key={i}
                className="flex items-center justify-between bg-[#12122a] rounded-md px-4 py-3 border border-[#2a2a4a]"
              >
                <div>
                  <div className="text-xs text-hud-muted">Wallet</div>
                  <div className="font-mono text-sm text-hud-text truncate max-w-[180px]">
                    {w.address}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold font-mono text-hud-accent">
                    {w.balance?.toFixed(2) ?? "0.00"}
                  </div>
                  {w.currency && (
                    <div className="text-xs text-hud-muted">{w.currency}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-hud-muted text-sm">No wallets found.</p>
        )}
      </div>

      {/* Available Services */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-3">
          Available Services
        </h3>
        {services.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {services.map((svc, i) => (
              <div
                key={i}
                className="bg-[#12122a] rounded-md px-4 py-3 border border-[#2a2a4a] hover:border-hud-accent/30 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-sm text-hud-accent">
                    {svc.name}
                  </span>
                  <span className="font-mono text-sm text-hud-text">
                    {svc.price ?? "—"}
                  </span>
                </div>
                {svc.description && (
                  <p className="text-xs text-hud-muted mb-2">{svc.description}</p>
                )}
                <button
                  onClick={() => handlePay(svc.name)}
                  disabled={paying === svc.name}
                  className="hud-btn w-full text-center disabled:opacity-50"
                >
                  {paying === svc.name ? "Processing..." : "Pay"}
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-hud-muted text-sm">No services available.</p>
        )}
      </div>

      {/* Payment History */}
      <div className="hud-card">
        <h3 className="text-sm font-semibold text-hud-muted uppercase tracking-wider mb-3">
          Payment History
        </h3>
        {payments.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-hud-muted text-xs uppercase">
                  <th className="pb-2 pr-4">Service</th>
                  <th className="pb-2 pr-4">Payer</th>
                  <th className="pb-2 pr-4">Amount</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p, i) => (
                  <tr key={i} className="hud-table-row">
                    <td className="py-2 pr-4 font-mono text-hud-accent">
                      {p.service}
                    </td>
                    <td className="py-2 pr-4 font-mono text-hud-muted">
                      {p.payer_wallet}
                    </td>
                    <td className="py-2 pr-4">{p.amount ?? "—"}</td>
                    <td className="py-2 pr-4">
                      <span
                        className={`text-xs font-mono ${
                          p.status === "success" || p.status === "completed"
                            ? "text-hud-success"
                            : p.status === "failed"
                              ? "text-hud-danger"
                              : "text-hud-warning"
                        }`}
                      >
                        {p.status}
                      </span>
                    </td>
                    <td className="py-2 text-hud-muted text-xs">
                      {p.timestamp ? new Date(p.timestamp).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-hud-muted text-sm">No payment history.</p>
        )}
      </div>
    </div>
  );
}
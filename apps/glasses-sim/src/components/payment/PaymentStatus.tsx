interface PaymentReceiptData {
  success: boolean;
  transactionId: string;
  amount: string;
  payer: string;
  payTo: string;
  resource: string;
  timestamp: number;
}

interface PaymentStatusProps {
  payment: PaymentReceiptData;
}

function weiToEth(wei: string): string {
  const val = Number(wei) / 1e18;
  return val.toFixed(6);
}

function shortenAddress(addr: string): string {
  if (addr.length <= 12) return addr;
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

export function PaymentStatus({ payment }: PaymentStatusProps) {
  return (
    <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-3 text-xs font-mono">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full bg-green-400" />
        <span className="text-green-400 font-bold text-[11px]">x402 PAYMENT</span>
      </div>

      <div className="space-y-1 text-hud-muted">
        <div className="flex justify-between">
          <span>Service</span>
          <span className="text-hud-text">{payment.resource}</span>
        </div>
        <div className="flex justify-between">
          <span>Amount</span>
          <span className="text-hud-accent">{weiToEth(payment.amount)} ETH</span>
        </div>
        <div className="flex justify-between">
          <span>From</span>
          <span className="text-hud-text">{shortenAddress(payment.payer)}</span>
        </div>
        <div className="flex justify-between">
          <span>To</span>
          <span className="text-hud-text">{shortenAddress(payment.payTo)}</span>
        </div>
        <div className="flex justify-between">
          <span>Tx</span>
          <span className="text-hud-accent">{shortenAddress(payment.transactionId)}</span>
        </div>
      </div>
    </div>
  );
}
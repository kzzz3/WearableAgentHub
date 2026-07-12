/**
 * x402 Payment Microservice
 *
 * Simulates the x402 payment protocol for WearableAgent Hub.
 * Runs as a standalone Hono HTTP service on port 8002.
 *
 * Flow:
 *   1. Client requests a paid service → receives 402 + payment requirements
 *   2. Client submits payment proof → server verifies + settles
 *   3. Service returns result with payment receipt
 *
 * For demo: uses in-memory mock wallets, no real blockchain.
 */

import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { cors } from "hono/cors";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PaymentRequirement {
  x402Version: number;
  accepts: PaymentOption[];
  resource: string;
  description: string;
}

interface PaymentOption {
  scheme: "exact";
  network: "base-sepolia";
  maxAmountRequired: string; // in atomic units (wei-like)
  resource: string;
  description: string;
  payTo: string;
  asset: string;
}

interface PaymentPayload {
  x402Version: number;
  scheme: "exact";
  network: "base-sepolia";
  payer: string;
  payTo: string;
  amount: string;
  resource: string;
  timestamp: number;
  nonce: string;
  signature: string;
}

interface PaymentReceipt {
  success: boolean;
  transactionId: string;
  amount: string;
  payer: string;
  payTo: string;
  resource: string;
  timestamp: number;
}

interface PaymentRecord {
  id: string;
  payer: string;
  payTo: string;
  amount: string;
  resource: string;
  description: string;
  status: "pending" | "verified" | "settled" | "failed";
  transactionId?: string;
  createdAt: number;
  settledAt?: number;
}

// ---------------------------------------------------------------------------
// Mock Data
// ---------------------------------------------------------------------------

const MOCK_WALLETS: Record<string, { address: string; balance: string }> = {
  user: { address: "0xUser1234567890abcdef1234567890abcdef12345678", balance: "1000000000000000000" },
  translator: { address: "0xTranslatorAbcDef1234567890abcdef1234567890ab", balance: "0" },
  navigator: { address: "0xNavigatorXyz78901234567890abcdef1234567890ab", balance: "0" },
};

const PAYMENT_SERVICES: Record<string, { price: string; payTo: string; description: string }> = {
  "translate": {
    price: "10000000000000000", // 0.01 ETH in wei
    payTo: MOCK_WALLETS.translator!.address,
    description: "Translation service (per request)",
  },
  "premium-nav": {
    price: "50000000000000000", // 0.05 ETH
    payTo: MOCK_WALLETS.navigator!.address,
    description: "Premium navigation with real-time traffic",
  },
  "health-analysis": {
    price: "20000000000000000", // 0.02 ETH
    payTo: MOCK_WALLETS.navigator!.address,
    description: "Detailed health data analysis",
  },
};

// In-memory payment history
const paymentHistory: PaymentRecord[] = [];
let txCounter = 0;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateTxId(): string {
  txCounter++;
  return `0xTx${String(txCounter).padStart(8, "0")}${Date.now().toString(16)}`;
}

function generateNonce(): string {
  return Math.random().toString(36).substring(2, 15);
}

function weiToEth(wei: string): string {
  const val = Number(wei) / 1e18;
  return val.toFixed(6);
}

// ---------------------------------------------------------------------------
// Hono App
// ---------------------------------------------------------------------------

const app = new Hono();

app.use("/*", cors({
  origin: "*",
  allowMethods: ["GET", "POST", "OPTIONS"],
  allowHeaders: ["Content-Type", "X-PAYMENT"],
}));

// Health
app.get("/health", (c) => c.json({ status: "ok", service: "x402-pay" }));

// ---------------------------------------------------------------------------
// x402 Protocol Endpoints
// ---------------------------------------------------------------------------

/**
 * GET /services — List available paid services
 */
app.get("/services", (c) => {
  const services = Object.entries(PAYMENT_SERVICES).map(([id, svc]) => ({
    id,
    description: svc.description,
    priceEth: weiToEth(svc.price),
    priceWei: svc.price,
    payTo: svc.payTo,
  }));
  return c.json({ services });
});

/**
 * POST /request-payment — Request payment requirements for a service
 * Body: { service: string }
 * Returns: 402 with PaymentRequirement (or 200 if free)
 */
app.post("/request-payment", async (c) => {
  const body = await c.req.json<{ service: string }>();
  const service = PAYMENT_SERVICES[body.service];

  if (!service) {
    return c.json({ error: `Unknown service: ${body.service}` }, 404);
  }

  const requirement: PaymentRequirement = {
    x402Version: 1,
    accepts: [
      {
        scheme: "exact",
        network: "base-sepolia",
        maxAmountRequired: service.price,
        resource: body.service,
        description: service.description,
        payTo: service.payTo,
        asset: "0x036CbD53842c5426634e7929541eC2318f3dCF7e", // USDC on base-sepolia (mock)
      },
    ],
    resource: body.service,
    description: service.description,
  };

  // Return 402 Payment Required
  return c.json(requirement, 402);
});

/**
 * POST /verify — Verify a payment payload
 * Body: { payment: PaymentPayload, requirement: PaymentRequirement }
 */
app.post("/verify", async (c) => {
  const body = await c.req.json<{ payment: PaymentPayload; requirement: PaymentRequirement }>();
  const { payment, requirement } = body;

  // Basic validation
  if (payment.x402Version !== 1) {
    return c.json({ valid: false, reason: "Invalid x402 version" });
  }

  if (!payment.signature || payment.signature.length < 10) {
    return c.json({ valid: false, reason: "Invalid signature" });
  }

  if (payment.amount !== requirement.accepts[0]!.maxAmountRequired) {
    return c.json({ valid: false, reason: "Amount mismatch" });
  }

  if (payment.payTo !== requirement.accepts[0]!.payTo) {
    return c.json({ valid: false, reason: "PayTo mismatch" });
  }

  // Record the payment
  const record: PaymentRecord = {
    id: generateTxId(),
    payer: payment.payer,
    payTo: payment.payTo,
    amount: payment.amount,
    resource: payment.resource,
    description: requirement.description,
    status: "verified",
    createdAt: Date.now(),
  };
  paymentHistory.push(record);

  return c.json({
    valid: true,
    paymentId: record.id,
    payer: payment.payer,
    amount: payment.amount,
  });
});

/**
 * POST /settle — Settle a verified payment
 * Body: { paymentId: string }
 */
app.post("/settle", async (c) => {
  const body = await c.req.json<{ paymentId: string }>();
  const record = paymentHistory.find((p) => p.id === body.paymentId);

  if (!record) {
    return c.json({ error: "Payment not found" }, 404);
  }

  if (record.status === "settled") {
    return c.json({ success: true, transactionId: record.transactionId, alreadySettled: true });
  }

  if (record.status !== "verified") {
    return c.json({ error: `Cannot settle payment in status: ${record.status}` }, 400);
  }

  // Simulate settlement
  const txId = generateTxId();
  record.status = "settled";
  record.transactionId = txId;
  record.settledAt = Date.now();

  // Update mock balances
  const payerWallet = Object.values(MOCK_WALLETS).find((w) => w.address === record.payer);
  const payeeWallet = Object.values(MOCK_WALLETS).find((w) => w.address === record.payTo);
  if (payerWallet) {
    payerWallet.balance = String(Number(payerWallet.balance) - Number(record.amount));
  }
  if (payeeWallet) {
    payeeWallet.balance = String(Number(payeeWallet.balance) + Number(record.amount));
  }

  const receipt: PaymentReceipt = {
    success: true,
    transactionId: txId,
    amount: record.amount,
    payer: record.payer,
    payTo: record.payTo,
    resource: record.resource,
    timestamp: record.settledAt,
  };

  return c.json(receipt);
});

/**
 * POST /pay-and-settle — One-shot: create payment, verify, settle
 * Body: { service: string, payerWallet?: string }
 * For demo convenience.
 */
app.post("/pay-and-settle", async (c) => {
  const body = await c.req.json<{ service: string; payerWallet?: string }>();
  const service = PAYMENT_SERVICES[body.service];

  if (!service) {
    return c.json({ error: `Unknown service: ${body.service}` }, 404);
  }

  const payerKey = body.payerWallet || "user";
  const payer = MOCK_WALLETS[payerKey];
  if (!payer) {
    return c.json({ error: `Unknown wallet: ${payerKey}` }, 404);
  }

  if (Number(payer.balance) < Number(service.price)) {
    return c.json({ error: "Insufficient balance", balance: payer.balance, required: service.price }, 402);
  }

  // Create mock payment
  const payment: PaymentPayload = {
    x402Version: 1,
    scheme: "exact",
    network: "base-sepolia",
    payer: payer.address,
    payTo: service.payTo,
    amount: service.price,
    resource: body.service,
    timestamp: Date.now(),
    nonce: generateNonce(),
    signature: `0xMockSig${Date.now().toString(16)}`,
  };

  // Record + settle
  const txId = generateTxId();
  const record: PaymentRecord = {
    id: txId,
    payer: payment.payer,
    payTo: payment.payTo,
    amount: payment.amount,
    resource: payment.resource,
    description: service.description,
    status: "settled",
    transactionId: txId,
    createdAt: Date.now(),
    settledAt: Date.now(),
  };
  paymentHistory.push(record);

  // Update balances
  payer.balance = String(Number(payer.balance) - Number(service.price));
  const payee = Object.values(MOCK_WALLETS).find((w) => w.address === service.payTo);
  if (payee) {
    payee.balance = String(Number(payee.balance) + Number(service.price));
  }

  const receipt: PaymentReceipt = {
    success: true,
    transactionId: txId,
    amount: service.price,
    payer: payment.payer,
    payTo: payment.payTo,
    resource: body.service,
    timestamp: record.settledAt!,
  };

  return c.json(receipt);
});

// ---------------------------------------------------------------------------
// Payment History / Dashboard
// ---------------------------------------------------------------------------

/**
 * GET /payments — List all payment records
 */
app.get("/payments", (c) => {
  return c.json({
    total: paymentHistory.length,
    payments: paymentHistory.map((p) => ({
      ...p,
      amountEth: weiToEth(p.amount),
    })),
  });
});

/**
 * GET /wallets — List mock wallet balances
 */
app.get("/wallets", (c) => {
  const wallets = Object.entries(MOCK_WALLETS).map(([name, w]) => ({
    name,
    address: w.address,
    balanceWei: w.balance,
    balanceEth: weiToEth(w.balance),
  }));
  return c.json({ wallets });
});

// ---------------------------------------------------------------------------
// Start Server
// ---------------------------------------------------------------------------

const port = Number(process.env.X402_PORT || 8002);

serve({ fetch: app.fetch, port }, (info) => {
  console.log(`[x402-pay] Payment service running on http://localhost:${info.port}`);
  console.log(`[x402-pay] Services: ${Object.keys(PAYMENT_SERVICES).join(", ")}`);
});

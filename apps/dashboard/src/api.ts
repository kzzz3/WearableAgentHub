const BASE = ""; // proxied by Vite dev server

export interface HealthResponse {
  status: string;
  [key: string]: unknown;
}

export interface Service {
  name: string;
  price: number;
  description?: string;
  [key: string]: unknown;
}

export interface Payment {
  id: string;
  service: string;
  payer_wallet: string;
  amount: number;
  timestamp: string;
  status: string;
  [key: string]: unknown;
}

export interface Wallet {
  address: string;
  balance: number;
  currency?: string;
  [key: string]: unknown;
}

export interface ChatResponse {
  reply: string;
  [key: string]: unknown;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return fetch(`${BASE}/health`).then((r) => r.json());
}

export async function fetchServices(): Promise<Service[]> {
  return fetch(`${BASE}/payment/services`).then((r) => r.json());
}

export async function payService(
  service: string,
  wallet = "user",
): Promise<Payment> {
  return fetch(
    `${BASE}/payment/pay?service=${encodeURIComponent(service)}&payer_wallet=${encodeURIComponent(wallet)}`,
    { method: "POST" },
  ).then((r) => r.json());
}

export async function fetchPaymentHistory(): Promise<Payment[]> {
  return fetch(`${BASE}/payment/history`).then((r) => r.json());
}

export async function fetchWallets(): Promise<Wallet[]> {
  return fetch(`${BASE}/payment/wallets`).then((r) => r.json());
}

export async function sendChat(
  message: string,
  sessionId = "dashboard",
): Promise<ChatResponse> {
  return fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  }).then((r) => r.json());
}
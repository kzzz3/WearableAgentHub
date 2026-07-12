import { create } from "zustand";
import type { A2UIMessage } from "@wearable-hub/a2ui-renderer";

interface PaymentReceipt {
  success: boolean;
  transactionId: string;
  amount: string;
  payer: string;
  payTo: string;
  resource: string;
  timestamp: number;
}

interface HistoryEntry {
  role: "user" | "assistant";
  text: string;
  source?: "local" | "a2a";
  payment?: PaymentReceipt | null;
}

interface HudState {
  connected: boolean;
  messages: A2UIMessage[];
  history: HistoryEntry[];
  isProcessing: boolean;
  setConnected: (v: boolean) => void;
  addA2UIMessages: (msgs: A2UIMessage[]) => void;
  addHistory: (entry: HistoryEntry) => void;
  setProcessing: (v: boolean) => void;
  clearMessages: () => void;
}

export type { PaymentReceipt, HistoryEntry };

export const useHudStore = create<HudState>((set) => ({
  connected: false,
  messages: [],
  history: [],
  isProcessing: false,
  setConnected: (v) => set({ connected: v }),
  addA2UIMessages: (msgs) => set((s) => ({ messages: [...s.messages, ...msgs] })),
  addHistory: (entry) => set((s) => ({ history: [...s.history, entry] })),
  setProcessing: (v) => set({ isProcessing: v }),
  clearMessages: () => set({ messages: [], history: [] }),
}));
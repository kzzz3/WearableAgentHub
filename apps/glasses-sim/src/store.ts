import { create } from "zustand";
import type { A2UIMessage } from "@wearable-hub/a2ui-renderer";

interface HudState {
  connected: boolean;
  messages: A2UIMessage[];
  history: Array<{ role: "user" | "assistant"; text: string }>;
  isProcessing: boolean;
  setConnected: (v: boolean) => void;
  addA2UIMessages: (msgs: A2UIMessage[]) => void;
  addHistory: (entry: { role: "user" | "assistant"; text: string }) => void;
  setProcessing: (v: boolean) => void;
  clearMessages: () => void;
}

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

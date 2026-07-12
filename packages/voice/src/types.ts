export type VoiceState = "idle" | "listening" | "thinking" | "speaking" | "error";

export interface VoiceMessage {
  type: "transcript" | "reply" | "a2ui" | "payment" | "status" | "error";
  content?: string;
  source?: string;
  messages?: unknown[];
  receipt?: unknown;
  state?: VoiceState;
  message?: string;
}
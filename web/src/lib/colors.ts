/* Classification color map — semantic colors used everywhere. */

import type { Classification, Confidence } from "./types";

export const classificationColors: Record<Classification, string> = {
  "RESEARCH CANDIDATE": "#22c55e",
  "QUALITY GROWTH PREMIUM": "#3b82f6",
  "WATCH LIST": "#eab308",
  HOLD: "#71717a",
  "OVERVALUED QUALITY": "#a78bfa",
  OVERVALUED: "#f97316",
  "VALUE TRAP": "#f43f5e",
  AVOID: "#a8a29e",
};

export const confidenceColors: Record<Confidence, string> = {
  HIGH: "#22c55e",
  MODERATE: "#eab308",
  LOW: "#ef4444",
};

export const confidenceIcons: Record<Confidence, string> = {
  HIGH: "▲",
  MODERATE: "●",
  LOW: "▼",
};

export function scoreColor(score: number): string {
  if (score >= 70) return "#22c55e";
  if (score >= 40) return "#eab308";
  return "#ef4444";
}

export function scoreBgOpacity(score: number): number {
  if (score >= 85) return 0.12;
  if (score >= 70) return 0.06;
  if (score >= 40) return 0.06;
  return 0.06;
}

import { useState, useEffect } from "react";
import { classificationColors } from "../../lib/colors";

interface DiffData {
  current_date: string;
  previous_date: string;
  new_picks: any[];
  dropped_picks: any[];
  changed_scores: any[];
}

export function WhatChanged() {
  const [diff, setDiff] = useState<DiffData | null>(null);

  useEffect(() => {
    fetch("/api/v1/screen/diff")
      .then((r) => { if (r.ok) return r.json(); throw new Error(); })
      .then(setDiff)
      .catch(() => {}); // Silently fail if <2 screens
  }, []);

  if (!diff) return null;
  if (diff.new_picks.length === 0 && diff.dropped_picks.length === 0 && diff.changed_scores.length === 0) return null;

  return (
    <div className="px-8 pb-6">
      <div className="rounded-lg p-5" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
        <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-4"
            style={{ color: "var(--color-text-muted)" }}>
          What Changed vs {diff.previous_date}
        </h3>

        {/* New picks */}
        {diff.new_picks.length > 0 && (
          <div className="mb-4">
            <div className="text-[12px] font-medium mb-2" style={{ color: "#22c55e" }}>
              New to Conviction Buy
            </div>
            {diff.new_picks.map((s: any) => (
              <div key={s.ticker} className="flex items-center gap-3 py-1.5">
                <span className="text-[13px]" style={{ color: "#22c55e" }}>+</span>
                <span className="font-mono text-[13px] font-semibold w-14">{s.ticker}</span>
                <span className="text-[12px] flex-1 truncate" style={{ color: "var(--color-text-secondary)" }}>{s.company}</span>
                <span className="font-mono text-[11px]" style={{ color: "var(--color-text-secondary)" }}>
                  V={Math.round(s.value_score)} Q={Math.round(s.quality_score)}
                </span>
                {s.confidence && (
                  <span className="text-[10px] font-mono" style={{ color: "#22c55e" }}>{s.confidence}</span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Dropped picks */}
        {diff.dropped_picks.length > 0 && (
          <div className="mb-4">
            <div className="text-[12px] font-medium mb-2" style={{ color: "#ef4444" }}>
              Dropped from Conviction Buy
            </div>
            {diff.dropped_picks.map((s: any) => {
              const newCl = s.new_classification;
              const clColor = newCl ? (classificationColors as any)[newCl] || "#71717a" : "#71717a";
              return (
                <div key={s.ticker} className="flex items-center gap-3 py-1.5">
                  <span className="text-[13px]" style={{ color: "#ef4444" }}>−</span>
                  <span className="font-mono text-[13px] font-semibold w-14">{s.ticker}</span>
                  <span className="text-[12px] flex-1 truncate" style={{ color: "var(--color-text-secondary)" }}>{s.company}</span>
                  {newCl && (
                    <span className="text-[10px] rounded-full px-2 py-0.5"
                          style={{ backgroundColor: `${clColor}20`, color: clColor }}>
                      → {newCl}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Score changes */}
        {diff.changed_scores.length > 0 && (
          <div>
            <div className="text-[12px] font-medium mb-2" style={{ color: "var(--color-text-secondary)" }}>
              Score Changes (still in CB)
            </div>
            {diff.changed_scores.map((s: any) => {
              const vDelta = s.current.value - s.previous.value;
              const qDelta = s.current.quality - s.previous.quality;
              return (
                <div key={s.ticker} className="flex items-center gap-3 py-1.5">
                  <span className="text-[13px]" style={{ color: "var(--color-text-muted)" }}>·</span>
                  <span className="font-mono text-[13px] font-semibold w-14">{s.ticker}</span>
                  <span className="font-mono text-[11px]" style={{ color: "var(--color-text-secondary)" }}>
                    V: {Math.round(s.previous.value)}→{Math.round(s.current.value)}
                    <span style={{ color: vDelta > 0 ? "#22c55e" : vDelta < 0 ? "#ef4444" : "var(--color-text-muted)" }}>
                      {vDelta > 0 ? " ↑" : vDelta < 0 ? " ↓" : " →"}
                    </span>
                    {"  "}Q: {Math.round(s.previous.quality)}→{Math.round(s.current.quality)}
                    <span style={{ color: qDelta > 0 ? "#22c55e" : qDelta < 0 ? "#ef4444" : "var(--color-text-muted)" }}>
                      {qDelta > 0 ? " ↑" : qDelta < 0 ? " ↓" : " →"}
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

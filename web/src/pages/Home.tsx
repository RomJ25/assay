import { useState } from "react";
import { useScreenData } from "../hooks/useScreenData";
import { SignalBanner } from "../components/dashboard/SignalBanner";
import { ConvictionTable } from "../components/picks/ConvictionTable";

export function Home() {
  const { data, loading, error } = useScreenData();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-48 h-1 rounded-full overflow-hidden" style={{ backgroundColor: "var(--color-surface-2)" }}>
          <div className="h-full rounded-full animate-pulse" style={{ backgroundColor: "var(--color-cb)", width: "40%" }} />
        </div>
        <p className="mt-4 text-[13px]" style={{ color: "var(--color-text-muted)" }}>Loading screen data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-8">
        <p className="text-lg mb-2" style={{ color: "#ef4444" }}>Unable to load screen data</p>
        <p className="text-[13px] mb-4" style={{ color: "var(--color-text-secondary)" }}>{error}</p>
        <p className="text-[13px]" style={{ color: "var(--color-text-muted)" }}>
          Run the screener first: <code className="font-mono">python main.py</code>
        </p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      <SignalBanner
        stocks={data.stocks}
        universe={data.universe}
        date={data.date}
        screened={data.screened}
      />

      <ConvictionTable stocks={data.stocks} onSelectStock={setSelectedTicker} />

      {/* Caveat footer */}
      <div className="text-center py-8 text-[12px] italic" style={{ color: "var(--color-text-muted)" }}>
        Research tool for idea generation. Not a trading signal. Minimum 3-5 year horizon.
      </div>

      {/* TODO: StockSheet deep dive panel */}
      {selectedTicker && (
        <div
          className="fixed inset-0 z-50 flex justify-end"
          onClick={() => setSelectedTicker(null)}
        >
          <div className="absolute inset-0" style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }} />
          <div
            className="relative w-[680px] h-full overflow-y-auto p-8"
            style={{ backgroundColor: "var(--color-surface-0)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="text-[13px] mb-6 hover:opacity-80"
              style={{ color: "var(--color-text-secondary)" }}
              onClick={() => setSelectedTicker(null)}
            >
              ← Back
            </button>
            <h2 className="font-mono text-2xl font-semibold mb-1">{selectedTicker}</h2>
            {(() => {
              const stock = data.stocks.find((s) => s.ticker === selectedTicker);
              if (!stock) return <p>Stock not found</p>;
              return (
                <div>
                  <p className="text-[13px] mb-4" style={{ color: "var(--color-text-secondary)" }}>
                    {stock.company} · {stock.sector}
                  </p>
                  <span
                    className="inline-flex rounded-full px-3 py-1 text-[13px] font-medium mb-6"
                    style={{
                      backgroundColor: `${classificationColor(stock.classification)}26`,
                      color: classificationColor(stock.classification),
                    }}
                  >
                    {stock.classification}
                    {stock.confidence && ` · ${stock.confidence}`}
                  </span>

                  {/* Score gauges placeholder */}
                  <div className="flex gap-4 my-6">
                    {[
                      { label: "Value", score: stock.value_score, sub: "EY rank" },
                      { label: "Quality", score: stock.quality_score, sub: "Pio+GP" },
                      { label: "Conviction", score: stock.conviction_score, sub: "√(V×Q)" },
                    ].map((g) => (
                      <div key={g.label} className="flex-1 rounded-lg p-4 text-center" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
                        <div className="text-[11px] uppercase tracking-wide mb-2" style={{ color: "var(--color-text-muted)" }}>{g.label}</div>
                        <div className="font-mono text-3xl font-semibold mb-1" style={{ color: "var(--color-text-primary)" }}>
                          {Math.round(g.score)}
                        </div>
                        <div className="text-[11px]" style={{ color: "var(--color-text-secondary)" }}>{g.sub}</div>
                      </div>
                    ))}
                  </div>

                  {/* Piotroski 3×3 grid */}
                  <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
                    Piotroski Breakdown · {stock.piotroski_f}/9
                  </h3>
                  <PiotroskiGrid breakdown={stock.piotroski_breakdown} />

                  {/* Value metrics */}
                  <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] mt-6 mb-3" style={{ color: "var(--color-text-muted)" }}>
                    Value Metrics
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: "EY%", value: stock.earnings_yield?.toFixed(1) },
                      { label: "FCF%", value: stock.fcf_yield?.toFixed(1) },
                      { label: "P/E", value: stock.pe_ratio?.toFixed(1) },
                      { label: "EV/EBITDA", value: stock.ev_ebitda?.toFixed(1) },
                      { label: "DCF Base", value: stock.dcf_base ? `$${Math.round(stock.dcf_base)}` : null },
                      { label: "Analyst", value: stock.analyst_target ? `$${Math.round(stock.analyst_target)}` : null },
                    ].map((m) => (
                      <div key={m.label} className="rounded-md p-3" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
                        <div className="text-[10px] uppercase tracking-wide mb-1" style={{ color: "var(--color-text-muted)" }}>{m.label}</div>
                        <div className="font-mono text-sm" style={{ color: "var(--color-text-primary)" }}>{m.value ?? "—"}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

function classificationColor(cl: string): string {
  const colors: Record<string, string> = {
    "CONVICTION BUY": "#22c55e",
    "QUALITY GROWTH PREMIUM": "#3b82f6",
    "WATCH LIST": "#eab308",
    HOLD: "#71717a",
    "OVERVALUED QUALITY": "#a78bfa",
    OVERVALUED: "#f97316",
    "VALUE TRAP": "#f43f5e",
    AVOID: "#a8a29e",
  };
  return colors[cl] || "#71717a";
}

const PIOTROSKI_LABELS = [
  ["Net Income", "Cash Flow", "ROA Trend"],
  ["Accruals", "Debt", "Liquidity"],
  ["Dilution", "Margins", "Turnover"],
];

const PIOTROSKI_KEYS = [
  ["net_income_positive", "ocf_positive", "roa_improving"],
  ["accruals_quality", "debt_ratio_decreasing", "current_ratio_up"],
  ["no_dilution", "gross_margin_up", "asset_turnover_up"],
];

const ROW_LABELS = ["Profitability", "Balance Sheet", "Efficiency"];

function PiotroskiGrid({ breakdown }: { breakdown: { raw_score: number; criteria: Record<string, { pass: boolean }> } }) {
  const criteria = breakdown?.criteria || {};

  return (
    <div className="space-y-1.5">
      {PIOTROSKI_KEYS.map((row, ri) => (
        <div key={ri} className="flex gap-1.5 items-center">
          {row.map((key, ci) => {
            const c = criteria[key];
            const pass = c?.pass ?? false;
            const color = pass ? "#22c55e" : "#ef4444";
            return (
              <div
                key={key}
                className="flex-1 rounded-lg p-2.5 text-center"
                style={{
                  backgroundColor: `${color}14`,
                  border: `1px solid ${color}33`,
                }}
              >
                <div className="text-base mb-0.5" style={{ color }}>{pass ? "✓" : "✗"}</div>
                <div className="text-[10px]" style={{ color: "var(--color-text-secondary)" }}>
                  {PIOTROSKI_LABELS[ri][ci]}
                </div>
              </div>
            );
          })}
          <span className="text-[10px] w-24 text-right italic" style={{ color: "var(--color-text-muted)" }}>
            {ROW_LABELS[ri]} ({row.filter((k) => criteria[k]?.pass).length}/3)
          </span>
        </div>
      ))}
    </div>
  );
}

import type { ScreenStock } from "../../lib/types";
import { classificationColors, confidenceColors, confidenceIcons, scoreColor } from "../../lib/colors";
import { fmtPrice, fmtMarketCap } from "../../lib/format";

interface Props {
  stocks: ScreenStock[];
  onClose: () => void;
}

const METRICS: { label: string; key: string; format: (s: ScreenStock) => string }[] = [
  { label: "Price", key: "price", format: (s) => fmtPrice(s.price) },
  { label: "Market Cap", key: "market_cap", format: (s) => fmtMarketCap(s.market_cap) },
  { label: "", key: "divider1", format: () => "" },
  { label: "Value Score", key: "value_score", format: (s) => Math.round(s.value_score).toString() },
  { label: "Quality Score", key: "quality_score", format: (s) => Math.round(s.quality_score).toString() },
  { label: "Conviction", key: "conviction_score", format: (s) => s.conviction_score.toFixed(1) },
  { label: "Confidence", key: "confidence", format: (s) => s.confidence || "—" },
  { label: "", key: "divider2", format: () => "" },
  { label: "F-Score", key: "piotroski_f", format: (s) => `${s.piotroski_f}/9` },
  { label: "Earnings Yield", key: "earnings_yield", format: (s) => s.earnings_yield != null ? `${s.earnings_yield.toFixed(1)}%` : "—" },
  { label: "FCF Yield", key: "fcf_yield", format: (s) => s.fcf_yield != null ? `${s.fcf_yield.toFixed(1)}%` : "—" },
  { label: "P/E", key: "pe_ratio", format: (s) => s.pe_ratio?.toFixed(1) ?? "—" },
  { label: "EV/EBITDA", key: "ev_ebitda", format: (s) => s.ev_ebitda?.toFixed(1) ?? "—" },
  { label: "", key: "divider3", format: () => "" },
  { label: "Gross Margin", key: "gross_margin", format: (s) => s.gross_margin != null ? `${(s.gross_margin * 100).toFixed(1)}%` : "—" },
  { label: "Revenue CAGR 3yr", key: "revenue_cagr_3yr", format: (s) => s.revenue_cagr_3yr != null ? `${(s.revenue_cagr_3yr * 100).toFixed(1)}%` : "—" },
  { label: "Momentum 12m", key: "momentum_12m", format: (s) => s.momentum_12m != null ? `${(s.momentum_12m * 100).toFixed(1)}%` : "—" },
  { label: "Trajectory", key: "trajectory_score", format: (s) => s.trajectory_score?.toFixed(0) ?? "—" },
  { label: "", key: "divider4", format: () => "" },
  { label: "Analyst Target", key: "analyst_target", format: (s) => s.analyst_target ? fmtPrice(s.analyst_target) : "—" },
  { label: "Analyst Upside", key: "analyst_upside", format: (s) => s.analyst_upside != null ? `${s.analyst_upside.toFixed(0)}%` : "—" },
  { label: "DCF Base", key: "dcf_base", format: (s) => s.dcf_base ? fmtPrice(s.dcf_base) : "—" },
  { label: "Dividend Yield", key: "dividend_yield", format: (s) => s.dividend_yield != null ? `${(s.dividend_yield * 100).toFixed(1)}%` : "—" },
];

function getNumeric(stock: ScreenStock, key: string): number | null {
  const val = (stock as unknown as Record<string, unknown>)[key];
  return typeof val === "number" ? val : null;
}

export function CompareView({ stocks, onClose }: Props) {
  // Find best value per metric for highlighting
  function isBest(metric: typeof METRICS[0], stock: ScreenStock): boolean {
    if (metric.key.startsWith("divider") || metric.key === "confidence") return false;
    const val = getNumeric(stock, metric.key);
    if (val == null) return false;
    const vals = stocks
      .map((s) => getNumeric(s, metric.key))
      .filter((v): v is number => v != null);
    if (vals.length < 2) return false;
    // Higher is better for most metrics, lower for P/E and EV/EBITDA
    if (metric.key === "pe_ratio" || metric.key === "ev_ebitda") {
      return val === Math.min(...vals) && val > 0;
    }
    return val === Math.max(...vals);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-8" onClick={onClose}>
      <div className="absolute inset-0" style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }} />
      <div className="relative max-w-4xl w-full max-h-[85vh] overflow-y-auto rounded-xl p-6"
           style={{ backgroundColor: "var(--color-surface-0)", border: "1px solid var(--color-border)" }}
           onClick={(e) => e.stopPropagation()}>

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-base font-semibold">Compare {stocks.length} Stocks</h2>
          <button className="text-[13px] hover:opacity-80" style={{ color: "var(--color-text-secondary)" }}
                  onClick={onClose}>✕ Close</button>
        </div>

        <table className="w-full">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--color-border)" }}>
              <th className="text-left text-[10px] uppercase tracking-[0.06em] py-2 px-2 w-36"
                  style={{ color: "var(--color-text-muted)" }}>Metric</th>
              {stocks.map((s) => {
                const clColor = classificationColors[s.classification] || "#71717a";
                return (
                  <th key={s.ticker} className="text-center py-2 px-2">
                    <div className="font-mono text-sm font-semibold">{s.ticker}</div>
                    <div className="text-[10px] truncate max-w-[120px] mx-auto" style={{ color: "var(--color-text-secondary)" }}>
                      {s.company}
                    </div>
                    <span className="inline-flex text-[9px] rounded-full px-1.5 py-0.5 mt-1 font-medium"
                          style={{ backgroundColor: `${clColor}20`, color: clColor }}>
                      {s.classification}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {METRICS.map((m) => {
              if (m.key.startsWith("divider")) {
                return (
                  <tr key={m.key}>
                    <td colSpan={stocks.length + 1} className="h-3" />
                  </tr>
                );
              }
              return (
                <tr key={m.key} className="border-b" style={{ borderColor: "rgba(39,39,42,0.3)" }}>
                  <td className="text-[11px] py-2 px-2" style={{ color: "var(--color-text-muted)" }}>{m.label}</td>
                  {stocks.map((s) => {
                    const best = isBest(m, s);
                    const isScore = ["value_score", "quality_score", "conviction_score"].includes(m.key);
                    const val = isScore ? getNumeric(s, m.key) : null;
                    return (
                      <td key={s.ticker} className="text-center font-mono text-[12px] py-2 px-2"
                          style={{ color: best ? "#22c55e" : "var(--color-text-primary)" }}>
                        {isScore && val != null ? (
                          <span className="rounded px-1.5 py-0.5"
                                style={{ backgroundColor: `${scoreColor(val)}${Math.round(0.06 * 255).toString(16).padStart(2, "0")}` }}>
                            {m.format(s)}
                          </span>
                        ) : (
                          m.key === "confidence" && s.confidence ? (
                            <span className="text-[10px] rounded-full px-1.5 py-0.5"
                                  style={{ backgroundColor: `${confidenceColors[s.confidence]}20`, color: confidenceColors[s.confidence] }}>
                              {confidenceIcons[s.confidence]} {s.confidence}
                            </span>
                          ) : m.format(s)
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}

            {/* Piotroski comparison row */}
            <tr>
              <td colSpan={stocks.length + 1} className="h-3" />
            </tr>
            <tr className="border-b" style={{ borderColor: "rgba(39,39,42,0.3)" }}>
              <td className="text-[11px] py-2 px-2" style={{ color: "var(--color-text-muted)" }}>Piotroski</td>
              {stocks.map((s) => (
                <td key={s.ticker} className="text-center py-2 px-2">
                  <div className="flex justify-center gap-0.5">
                    {["net_income_positive", "ocf_positive", "roa_improving",
                      "accruals_quality", "debt_ratio_decreasing", "current_ratio_up",
                      "no_dilution", "gross_margin_up", "asset_turnover_up"].map((key) => {
                      const pass = s.piotroski_breakdown?.criteria?.[key]?.pass ?? false;
                      return (
                        <div key={key} className="w-2 h-2 rounded-sm"
                             style={{ backgroundColor: pass ? "#22c55e" : "#ef4444", opacity: 0.7 }} />
                      );
                    })}
                  </div>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

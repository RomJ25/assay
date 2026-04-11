import { useState, useEffect } from "react";
import type { ScreenStock, Classification, Confidence } from "../../lib/types";
import { classificationColors, confidenceColors, confidenceIcons, scoreColor } from "../../lib/colors";
import { fmtPrice, fmtMarketCap } from "../../lib/format";

interface Props {
  stock: ScreenStock;
  allStocks?: ScreenStock[]; // Pass all stocks for peer analysis
  onClose: () => void;
}

export function StockSheet({ stock, allStocks, onClose }: Props) {
  const [tab, setTab] = useState<"detail" | "peers">("detail");
  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const clColor = classificationColors[stock.classification] || "#71717a";
  const isCB = stock.classification === "CONVICTION BUY";

  return (
    <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 transition-opacity duration-200"
           style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }} />

      {/* Panel */}
      <div
        className="relative w-full max-w-[680px] h-full overflow-y-auto border-l"
        style={{ backgroundColor: "var(--color-surface-0)", borderColor: "var(--color-border)" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Brand color top border */}
        <div className="h-0.5" style={{ backgroundColor: clColor }} />

        <div className="p-8">
          {/* Back button */}
          <button className="text-[13px] mb-6 hover:opacity-80 transition-opacity"
                  style={{ color: "var(--color-text-secondary)" }} onClick={onClose}>
            ← Back
          </button>

          {/* Header */}
          <div className="mb-6">
            <h2 className="font-mono text-3xl font-semibold mb-1">{stock.ticker}</h2>
            <p className="text-[13px] mb-3" style={{ color: "var(--color-text-secondary)" }}>
              {stock.company} · {stock.sector}
            </p>
            <p className="font-mono text-sm mb-4" style={{ color: "var(--color-text-secondary)" }}>
              {fmtPrice(stock.price)} · {fmtMarketCap(stock.market_cap)}
            </p>

            {/* Classification + Confidence badges */}
            <div className="flex items-center gap-2">
              <span className="inline-flex rounded-full px-3 py-1 text-[12px] font-medium"
                    style={{ backgroundColor: `${clColor}26`, color: clColor }}>
                {stock.classification}
              </span>
              {stock.confidence && (
                <span className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium"
                      style={{
                        backgroundColor: `${confidenceColors[stock.confidence]}26`,
                        color: confidenceColors[stock.confidence],
                      }}>
                  {confidenceIcons[stock.confidence]} {stock.confidence}
                </span>
              )}
            </div>
          </div>

          {/* ── WHY THIS STOCK QUALIFIES (narrative) ── */}
          {isCB && <Narrative stock={stock} />}
          {!isCB && <NonCBNarrative stock={stock} />}

          {/* ── Score gauges ── */}
          <SectionLabel>Scores</SectionLabel>
          <div className="flex gap-3 mb-6">
            {([
              { label: "Value", score: stock.value_score, sub: `${Math.round(stock.value_score)}th percentile by earnings yield` },
              { label: "Quality", score: stock.quality_score, sub: `Piotroski ${stock.piotroski_f}/9 + gross profitability` },
              { label: "Conviction", score: stock.conviction_score, sub: "Geometric mean — both must be high" },
            ] as const).map((g) => (
              <div key={g.label} className="flex-1 rounded-lg p-4 text-center"
                   style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
                <div className="text-[10px] uppercase tracking-[0.06em] mb-2" style={{ color: "var(--color-text-muted)" }}>
                  {g.label}
                </div>
                <div className="font-mono text-3xl font-semibold mb-1.5"
                     style={{ color: scoreColor(g.score) }}>
                  {Math.round(g.score)}
                </div>
                <div className="text-[10px] leading-tight" style={{ color: "var(--color-text-secondary)" }}>
                  {g.sub}
                </div>
              </div>
            ))}
          </div>

          {/* ── Gate status ── */}
          {isCB && <GateStatus stock={stock} />}

          {/* ── Piotroski 3×3 ── */}
          <SectionLabel>Piotroski Breakdown · {stock.piotroski_f}/9</SectionLabel>
          <PiotroskiGrid breakdown={stock.piotroski_breakdown} />

          {/* ── Value Metrics ── */}
          <SectionLabel className="mt-6">Value Metrics</SectionLabel>
          <MetricsGrid metrics={[
            { label: "Earnings Yield", value: stock.earnings_yield != null ? `${stock.earnings_yield.toFixed(1)}%` : null },
            { label: "FCF Yield", value: stock.fcf_yield != null ? `${stock.fcf_yield.toFixed(1)}%` : null },
            { label: "P/E", value: stock.pe_ratio?.toFixed(1) ?? null },
            { label: "EV/EBITDA", value: stock.ev_ebitda?.toFixed(1) ?? null },
            { label: "Dividend", value: stock.dividend_yield != null ? `${(stock.dividend_yield * 100).toFixed(1)}%` : null },
            { label: "Beta", value: stock.beta?.toFixed(2) ?? null },
          ]} />

          {/* ── Valuation ── */}
          {(stock.dcf_base || stock.analyst_target) && (
            <>
              <SectionLabel className="mt-6">Valuation Context</SectionLabel>
              <div className="space-y-3">
                {stock.dcf_base && <DCFRange stock={stock} />}
                {stock.analyst_target && (
                  <div className="rounded-lg p-3" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
                    <div className="text-[10px] uppercase tracking-[0.06em] mb-1" style={{ color: "var(--color-text-muted)" }}>
                      Analyst Consensus
                    </div>
                    <div className="font-mono text-sm">
                      {fmtPrice(stock.analyst_target)}
                      {stock.analyst_upside != null && (
                        <span style={{ color: stock.analyst_upside >= 0 ? "#22c55e" : "#ef4444" }}>
                          {" "}({stock.analyst_upside >= 0 ? "+" : ""}{stock.analyst_upside.toFixed(0)}% upside)
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* ── Momentum & Trajectory ── */}
          <SectionLabel className="mt-6">Momentum & Trajectory</SectionLabel>
          <MetricsGrid metrics={[
            { label: "12-1 Month Return", value: stock.momentum_12m != null ? `${(stock.momentum_12m * 100).toFixed(1)}%` : null },
            { label: "Trajectory", value: stock.trajectory_score?.toFixed(0) ?? null },
            { label: "Revenue CAGR 3yr", value: stock.revenue_cagr_3yr != null ? `${(stock.revenue_cagr_3yr * 100).toFixed(1)}%` : null },
            { label: "Gross Margin", value: stock.gross_margin != null ? `${(stock.gross_margin * 100).toFixed(1)}%` : null },
            { label: "Gross Profitability", value: stock.gross_profitability?.toFixed(3) ?? null },
            { label: "Growth Score", value: stock.growth_score?.toFixed(0) ?? null },
          ]} />

          {/* ── Sector Peers ── */}
          {allStocks && <SectorPeers stock={stock} allStocks={allStocks} />}
        </div>
      </div>
    </div>
  );
}

/* ── Narrative: WHY THIS STOCK QUALIFIES ── */

function Narrative({ stock }: { stock: ScreenStock }) {
  return (
    <div className="rounded-lg p-5 mb-6" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <div className="text-[11px] uppercase tracking-[0.06em] mb-3 font-medium"
           style={{ color: "var(--color-cb)" }}>
        Why This Stock Qualifies
      </div>
      <ol className="space-y-2 text-[13px] list-decimal list-inside" style={{ color: "var(--color-text-secondary)" }}>
        <li>
          <strong style={{ color: "var(--color-text-primary)" }}>Cheap:</strong> ranked{" "}
          <span className="font-mono">{Math.round(stock.value_score)}th</span> percentile by earnings yield
          {stock.earnings_yield != null && <> (<span className="font-mono">{stock.earnings_yield.toFixed(1)}%</span> EY)</>}
        </li>
        <li>
          <strong style={{ color: "var(--color-text-primary)" }}>High quality:</strong> ranked{" "}
          <span className="font-mono">{Math.round(stock.quality_score)}th</span> percentile
          — Piotroski <span className="font-mono">{stock.piotroski_f}/9</span>
          {stock.gross_profitability != null && <> + GP/Assets <span className="font-mono">{stock.gross_profitability.toFixed(2)}</span></>}
        </li>
        <li>
          <strong style={{ color: "var(--color-text-primary)" }}>Both dimensions strong:</strong> conviction{" "}
          <span className="font-mono">{stock.conviction_score.toFixed(1)}</span>
          {" "}(geometric mean ensures neither can be weak)
        </li>
        <li>
          <strong style={{ color: "var(--color-text-primary)" }}>Passed safety gates:</strong>{" "}
          F-Score <span className="font-mono">{stock.piotroski_f}/9</span> (≥6 required) ✓
          {stock.momentum_12m != null && (
            <> · Momentum <span className="font-mono">{(stock.momentum_12m * 100).toFixed(0)}%</span> (&gt;25th pctl) ✓</>
          )}
        </li>
        {stock.confidence && (
          <li>
            <strong style={{ color: "var(--color-text-primary)" }}>
              {stock.confidence} confidence:
            </strong>{" "}
            {stock.confidence === "HIGH" && "both scores 15+ points above threshold"}
            {stock.confidence === "MODERATE" && "both scores 5+ points above threshold"}
            {stock.confidence === "LOW" && "at least one score barely above 70 threshold"}
          </li>
        )}
      </ol>
    </div>
  );
}

function NonCBNarrative({ stock }: { stock: ScreenStock }) {
  const cl = stock.classification;
  let reason = "";
  if (cl === "WATCH LIST") {
    if (stock.value_score >= 70 && stock.quality_score >= 70) {
      if (stock.piotroski_f < 6) reason = `Would be CB but F-Score is ${stock.piotroski_f}/9 (minimum 6 required).`;
      else reason = "Would be CB but caught by momentum gate (bottom 25%).";
    } else {
      reason = `Value ${Math.round(stock.value_score)} is high but Quality ${Math.round(stock.quality_score)} is mid-range (needs ≥70 for CB).`;
    }
  } else if (cl === "VALUE TRAP") {
    reason = `Cheap (V=${Math.round(stock.value_score)}) but low quality (Q=${Math.round(stock.quality_score)}). The value may be a mirage.`;
  } else if (cl === "QUALITY GROWTH PREMIUM") {
    reason = `High quality (Q=${Math.round(stock.quality_score)}) but not cheap enough (V=${Math.round(stock.value_score)}, needs ≥70).`;
  } else if (cl === "OVERVALUED QUALITY") {
    reason = `Excellent quality (Q=${Math.round(stock.quality_score)}) but expensive (V=${Math.round(stock.value_score)}).`;
  } else if (cl === "OVERVALUED") {
    reason = `Expensive (V=${Math.round(stock.value_score)}) with moderate quality (Q=${Math.round(stock.quality_score)}).`;
  } else if (cl === "HOLD") {
    reason = `Mid-range on both dimensions (V=${Math.round(stock.value_score)}, Q=${Math.round(stock.quality_score)}).`;
  } else if (cl === "AVOID") {
    reason = `Neither cheap nor high quality (V=${Math.round(stock.value_score)}, Q=${Math.round(stock.quality_score)}).`;
  }

  return (
    <div className="rounded-lg p-4 mb-6" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <div className="text-[13px]" style={{ color: "var(--color-text-secondary)" }}>
        {reason}
      </div>
    </div>
  );
}

/* ── Gate Status ── */

function GateStatus({ stock }: { stock: ScreenStock }) {
  return (
    <div className="mb-6">
      <SectionLabel>Safety Gates</SectionLabel>
      <div className="space-y-2">
        <GateRow
          label="F-Score Gate"
          passed={stock.piotroski_f >= 6}
          detail={`F = ${stock.piotroski_f}/9 (minimum 6 required)`}
        />
        <GateRow
          label="Momentum Gate"
          passed={true}
          detail={stock.momentum_12m != null
            ? `12-1 month return: ${(stock.momentum_12m * 100).toFixed(1)}% (above 25th percentile cutoff)`
            : "Momentum data available"}
        />
      </div>
    </div>
  );
}

function GateRow({ label, passed, detail }: { label: string; passed: boolean; detail: string }) {
  const color = passed ? "#22c55e" : "#ef4444";
  return (
    <div className="flex items-center gap-3 rounded-md px-3 py-2"
         style={{ backgroundColor: `${color}08`, border: `1px solid ${color}1a` }}>
      <span className="text-sm" style={{ color }}>{passed ? "✓" : "✗"}</span>
      <div>
        <span className="text-[12px] font-medium" style={{ color: "var(--color-text-primary)" }}>
          {label}: {passed ? "PASSED" : "FIRED"}
        </span>
        <span className="text-[11px] ml-2" style={{ color: "var(--color-text-secondary)" }}>
          {detail}
        </span>
      </div>
    </div>
  );
}

/* ── DCF Range Bar ── */

function DCFRange({ stock }: { stock: ScreenStock }) {
  if (!stock.dcf_bear || !stock.dcf_base || !stock.dcf_bull) return null;

  const min = stock.dcf_bear * 0.9;
  const max = stock.dcf_bull * 1.1;
  const range = max - min;
  const bearPct = ((stock.dcf_bear - min) / range) * 100;
  const basePct = ((stock.dcf_base - min) / range) * 100;
  const bullPct = ((stock.dcf_bull - min) / range) * 100;
  const pricePct = ((stock.price - min) / range) * 100;

  return (
    <div className="rounded-lg p-4" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <div className="text-[10px] uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
        DCF Scenarios vs Current Price
      </div>
      <div className="relative h-8 mb-2">
        {/* Range bar */}
        <div className="absolute top-3 h-2 rounded-full"
             style={{ left: `${bearPct}%`, width: `${bullPct - bearPct}%`, backgroundColor: "var(--color-surface-3)" }} />
        {/* Base marker */}
        <div className="absolute top-2 w-1 h-4 rounded-full"
             style={{ left: `${basePct}%`, backgroundColor: "var(--color-text-secondary)" }} />
        {/* Current price marker */}
        <div className="absolute top-0 w-0.5 h-8"
             style={{ left: `${Math.min(Math.max(pricePct, 0), 100)}%`, backgroundColor: "#60a5fa" }} />
      </div>
      <div className="flex justify-between text-[11px] font-mono" style={{ color: "var(--color-text-secondary)" }}>
        <span>Bear {fmtPrice(stock.dcf_bear)}</span>
        <span>Base {fmtPrice(stock.dcf_base)}</span>
        <span>Bull {fmtPrice(stock.dcf_bull)}</span>
      </div>
      <div className="text-[11px] mt-1 font-mono" style={{ color: "#60a5fa" }}>
        Current {fmtPrice(stock.price)}
        {stock.dcf_base && (
          <span style={{ color: "var(--color-text-muted)" }}>
            {" "}({stock.price > stock.dcf_base
              ? `${((stock.price / stock.dcf_base - 1) * 100).toFixed(0)}% above base`
              : `${((1 - stock.price / stock.dcf_base) * 100).toFixed(0)}% below base`})
          </span>
        )}
      </div>
    </div>
  );
}

/* ── Piotroski 3×3 Grid ── */

const PIO_KEYS = [
  ["net_income_positive", "ocf_positive", "roa_improving"],
  ["accruals_quality", "debt_ratio_decreasing", "current_ratio_up"],
  ["no_dilution", "gross_margin_up", "asset_turnover_up"],
];

const PIO_LABELS = [
  ["Net Income", "Cash Flow", "ROA Trend"],
  ["Accruals", "Debt", "Liquidity"],
  ["Dilution", "Margins", "Turnover"],
];

const PIO_ROW_LABELS = ["Profitability", "Balance Sheet", "Efficiency"];

function PiotroskiGrid({ breakdown }: { breakdown: ScreenStock["piotroski_breakdown"] }) {
  const criteria = breakdown?.criteria || {};

  return (
    <div className="space-y-1.5 mb-6">
      {PIO_KEYS.map((row, ri) => {
        const rowPassed = row.filter((k) => criteria[k]?.pass).length;
        return (
          <div key={ri} className="flex gap-1.5 items-center">
            {row.map((key, ci) => {
              const c = criteria[key];
              const pass = c?.pass ?? false;
              const color = pass ? "#22c55e" : "#ef4444";
              return (
                <div key={key} className="flex-1 rounded-lg p-2.5 text-center transition-transform duration-150 hover:scale-[1.02]"
                     style={{ backgroundColor: `${color}14`, border: `1px solid ${color}33` }}>
                  <div className="text-base mb-0.5" style={{ color }}>{pass ? "✓" : "✗"}</div>
                  <div className="text-[10px]" style={{ color: "var(--color-text-secondary)" }}>
                    {PIO_LABELS[ri][ci]}
                  </div>
                </div>
              );
            })}
            <span className="text-[10px] w-28 text-right italic" style={{ color: "var(--color-text-muted)" }}>
              {PIO_ROW_LABELS[ri]} ({rowPassed}/3)
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ── Shared Components ── */

function SectionLabel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <h3 className={`text-[11px] font-medium uppercase tracking-[0.06em] mb-3 ${className}`}
        style={{ color: "var(--color-text-muted)" }}>
      {children}
    </h3>
  );
}

function MetricsGrid({ metrics }: { metrics: { label: string; value: string | null }[] }) {
  return (
    <div className="grid grid-cols-3 gap-2 mb-6">
      {metrics.map((m) => (
        <div key={m.label} className="rounded-md p-3"
             style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
          <div className="text-[10px] uppercase tracking-[0.04em] mb-1" style={{ color: "var(--color-text-muted)" }}>
            {m.label}
          </div>
          <div className="font-mono text-sm" style={{ color: "var(--color-text-primary)" }}>
            {m.value ?? "—"}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Sector Peers ── */

function SectorPeers({ stock, allStocks }: { stock: ScreenStock; allStocks: ScreenStock[] }) {
  const peers = allStocks
    .filter((s) => s.sector === stock.sector && s.ticker !== stock.ticker)
    .sort((a, b) => (b.conviction_score || 0) - (a.conviction_score || 0))
    .slice(0, 15);

  if (peers.length === 0) return null;

  // Sector medians
  const sectorStocks = allStocks.filter((s) => s.sector === stock.sector);
  const median = (arr: number[]) => {
    const sorted = [...arr].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  };

  const peValues = sectorStocks.map((s) => s.pe_ratio).filter((v): v is number => v != null);
  const eyValues = sectorStocks.map((s) => s.earnings_yield).filter((v): v is number => v != null);
  const medianPE = peValues.length > 0 ? median(peValues) : null;
  const medianEY = eyValues.length > 0 ? median(eyValues) : null;

  return (
    <div>
      <SectionLabel className="mt-6">
        Sector Peers · {stock.sector} ({sectorStocks.length} stocks)
      </SectionLabel>

      {/* Sector medians */}
      {(medianPE || medianEY) && (
        <div className="flex gap-4 mb-3 text-[11px]" style={{ color: "var(--color-text-secondary)" }}>
          {medianPE && <span>Sector Median P/E: <span className="font-mono">{medianPE.toFixed(1)}</span></span>}
          {medianEY && <span>Sector Median EY: <span className="font-mono">{medianEY.toFixed(1)}%</span></span>}
          {stock.pe_ratio && medianPE && (
            <span>
              {stock.ticker} discount:{" "}
              <span className="font-mono" style={{ color: stock.pe_ratio < medianPE ? "#22c55e" : "#ef4444" }}>
                {((1 - stock.pe_ratio / medianPE) * 100).toFixed(0)}%
              </span>
            </span>
          )}
        </div>
      )}

      {/* Peer table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--color-surface-3)" }}>
              {["Ticker", "Company", "Class", "V", "Q", "Conv", "F", "EY%"].map((h) => (
                <th key={h} className={`text-[9px] font-medium uppercase tracking-[0.06em] py-2 px-1.5 ${
                  ["V", "Q", "Conv", "F", "EY%"].includes(h) ? "text-right" : "text-left"
                }`} style={{ color: "var(--color-text-muted)" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* Current stock highlighted */}
            <tr className="border-b" style={{ borderColor: "rgba(39,39,42,0.5)", backgroundColor: "var(--color-surface-1)" }}>
              <td className="font-mono text-[11px] font-semibold py-1.5 px-1.5" style={{ color: "#60a5fa" }}>{stock.ticker} ←</td>
              <td className="text-[11px] py-1.5 px-1.5 truncate max-w-[120px]" style={{ color: "var(--color-text-secondary)" }}>{stock.company}</td>
              <td className="py-1.5 px-1.5"><ClassBadge cl={stock.classification} /></td>
              <td className="font-mono text-[11px] py-1.5 px-1.5 text-right">{Math.round(stock.value_score)}</td>
              <td className="font-mono text-[11px] py-1.5 px-1.5 text-right">{Math.round(stock.quality_score)}</td>
              <td className="font-mono text-[11px] py-1.5 px-1.5 text-right font-medium">{stock.conviction_score.toFixed(1)}</td>
              <td className="font-mono text-[11px] py-1.5 px-1.5 text-right">{stock.piotroski_f}/9</td>
              <td className="font-mono text-[11px] py-1.5 px-1.5 text-right">{stock.earnings_yield?.toFixed(1) ?? "—"}%</td>
            </tr>
            {/* Peers */}
            {peers.map((p) => (
              <tr key={p.ticker} className="border-b" style={{ borderColor: "rgba(39,39,42,0.3)" }}>
                <td className="font-mono text-[11px] py-1.5 px-1.5">{p.ticker}</td>
                <td className="text-[11px] py-1.5 px-1.5 truncate max-w-[120px]" style={{ color: "var(--color-text-secondary)" }}>{p.company}</td>
                <td className="py-1.5 px-1.5"><ClassBadge cl={p.classification} /></td>
                <td className="font-mono text-[11px] py-1.5 px-1.5 text-right">{Math.round(p.value_score)}</td>
                <td className="font-mono text-[11px] py-1.5 px-1.5 text-right">{Math.round(p.quality_score)}</td>
                <td className="font-mono text-[11px] py-1.5 px-1.5 text-right">{p.conviction_score.toFixed(1)}</td>
                <td className="font-mono text-[11px] py-1.5 px-1.5 text-right" style={{ color: "var(--color-text-muted)" }}>{p.piotroski_f}/9</td>
                <td className="font-mono text-[11px] py-1.5 px-1.5 text-right" style={{ color: "var(--color-text-muted)" }}>{p.earnings_yield?.toFixed(1) ?? "—"}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ClassBadge({ cl }: { cl: Classification }) {
  const color = classificationColors[cl] || "#71717a";
  const SHORT: Record<string, string> = {
    "CONVICTION BUY": "CB", "QUALITY GROWTH PREMIUM": "QGP", "WATCH LIST": "WL",
    HOLD: "HOLD", "OVERVALUED QUALITY": "OQ", OVERVALUED: "OV", "VALUE TRAP": "VT", AVOID: "AV",
  };
  return (
    <span className="text-[9px] font-mono font-medium rounded px-1 py-0.5"
          style={{ backgroundColor: `${color}20`, color }}>
      {SHORT[cl] || cl}
    </span>
  );
}

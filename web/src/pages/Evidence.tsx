import { useMemo } from "react";
import { useBacktestData } from "../hooks/useBacktestData";

export function Evidence() {
  const { data, loading, error } = useBacktestData();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-[13px]" style={{ color: "var(--color-text-muted)" }}>Loading backtest data...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-8">
        <p className="text-lg mb-2" style={{ color: "#ef4444" }}>No backtest data available</p>
        <p className="text-[13px]" style={{ color: "var(--color-text-secondary)" }}>
          Run: <code className="font-mono">python main.py --backtest</code>
        </p>
      </div>
    );
  }

  return (
    <div className="px-8 py-10">
      <h1 className="text-xl font-semibold mb-1">Evidence</h1>
      <p className="text-[13px] mb-8" style={{ color: "var(--color-text-secondary)" }}>
        Historical backtest results and systematic investigation findings.
      </p>

      {/* Limitations banner */}
      <div className="rounded-lg p-4 mb-8" style={{ backgroundColor: "#eab30808", border: "1px solid #eab30820" }}>
        <div className="text-[11px] uppercase tracking-[0.06em] mb-2 font-medium" style={{ color: "#eab308" }}>
          Known Limitations
        </div>
        <ul className="text-[12px] space-y-1" style={{ color: "var(--color-text-secondary)" }}>
          <li>Survivorship bias: uses current S&P 500 list (est. 2-5% CAGR overstatement)</li>
          <li>Sample size: {data.quarters.length} quarters (below 30-period minimum for statistical significance)</li>
          <li>Data: Yahoo Finance (may include retroactive restatements)</li>
        </ul>
      </div>

      {/* Performance Summary */}
      <PerformanceSummary quarters={data.quarters} />

      {/* Cumulative Chart */}
      <CumulativeChart quarters={data.quarters} />

      {/* Quarterly Table */}
      <QuarterlyTable quarters={data.quarters} />

      {/* Investigation Summary */}
      <InvestigationSummary />
    </div>
  );
}

/* ── Performance Summary Cards ── */

function PerformanceSummary({ quarters }: { quarters: any[] }) {
  const stats = useMemo(() => {
    let portVal = 1, univVal = 1, spyVal = 1;
    let maxPort = 1, maxDD = 0;
    const qReturns: number[] = [];

    for (const q of quarters) {
      const pr = q.portfolio_return / 100;
      const ur = q.universe_return / 100;
      const sr = q.spy_return / 100;
      portVal *= (1 + pr);
      univVal *= (1 + ur);
      spyVal *= (1 + sr);
      qReturns.push(pr);
      if (portVal > maxPort) maxPort = portVal;
      const dd = (maxPort - portVal) / maxPort;
      if (dd > maxDD) maxDD = dd;
    }

    const years = quarters.length / 4;
    const cagr = (pv: number) => years > 0 && pv > 0 ? pv ** (1 / years) - 1 : 0;

    return {
      totalReturn: portVal - 1,
      univReturn: univVal - 1,
      spyReturn: spyVal - 1,
      cagr: cagr(portVal),
      univCagr: cagr(univVal),
      spyCagr: cagr(spyVal),
      maxDD: -maxDD,
      selectionAlpha: cagr(portVal) - cagr(univVal),
      quarters: quarters.length,
    };
  }, [quarters]);

  return (
    <div className="mb-8">
      <h2 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
        Performance Summary
      </h2>
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Portfolio", cagr: stats.cagr, total: stats.totalReturn },
          { label: "Universe (EW)", cagr: stats.univCagr, total: stats.univReturn },
          { label: "S&P 500 (SPY)", cagr: stats.spyCagr, total: stats.spyReturn },
        ].map((c) => (
          <div key={c.label} className="rounded-lg p-4"
               style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
            <div className="text-[10px] uppercase tracking-[0.06em] mb-2" style={{ color: "var(--color-text-muted)" }}>
              {c.label}
            </div>
            <div className="font-mono text-2xl font-semibold mb-1"
                 style={{ color: c.cagr >= 0 ? "#22c55e" : "#ef4444" }}>
              {(c.cagr * 100).toFixed(1)}%
            </div>
            <div className="text-[11px]" style={{ color: "var(--color-text-secondary)" }}>
              CAGR · Total: {(c.total * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3 mt-3">
        <MetricCard label="Selection Alpha" value={`${(stats.selectionAlpha * 100).toFixed(1)}%`}
                    color={stats.selectionAlpha >= 0 ? "#22c55e" : "#ef4444"} sub="Portfolio CAGR - Universe CAGR" />
        <MetricCard label="Max Drawdown" value={`${(stats.maxDD * 100).toFixed(1)}%`}
                    color="#ef4444" sub="Peak-to-trough" />
        <MetricCard label="Quarters" value={`${stats.quarters}`}
                    color="var(--color-text-primary)" sub={stats.quarters < 30 ? "Below 30-quarter minimum" : "Statistical sample"} />
      </div>
    </div>
  );
}

function MetricCard({ label, value, color, sub }: { label: string; value: string; color: string; sub: string }) {
  return (
    <div className="rounded-lg p-4" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <div className="text-[10px] uppercase tracking-[0.06em] mb-2" style={{ color: "var(--color-text-muted)" }}>{label}</div>
      <div className="font-mono text-xl font-semibold mb-1" style={{ color }}>{value}</div>
      <div className="text-[10px]" style={{ color: "var(--color-text-secondary)" }}>{sub}</div>
    </div>
  );
}

/* ── Cumulative Return Chart (text-based for now, Recharts upgrade later) ── */

function CumulativeChart({ quarters }: { quarters: any[] }) {
  const data = useMemo(() => {
    let portVal = 1, univVal = 1, spyVal = 1;
    return quarters.map((q) => {
      portVal *= (1 + q.portfolio_return / 100);
      univVal *= (1 + q.universe_return / 100);
      spyVal *= (1 + q.spy_return / 100);
      return {
        date: q.date,
        portfolio: ((portVal - 1) * 100).toFixed(1),
        universe: ((univVal - 1) * 100).toFixed(1),
        spy: ((spyVal - 1) * 100).toFixed(1),
        picks: q.num_picks,
      };
    });
  }, [quarters]);

  return (
    <div className="rounded-lg p-4 mb-8" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
        Cumulative Returns
      </h3>
      <div className="overflow-x-auto">
        <div className="flex gap-6 text-[11px] mb-3">
          <span><span className="inline-block w-3 h-0.5 rounded mr-1" style={{ backgroundColor: "#d4a832" }} /> Portfolio</span>
          <span><span className="inline-block w-3 h-0.5 rounded mr-1" style={{ backgroundColor: "#71717a" }} /> Universe</span>
          <span><span className="inline-block w-3 h-0.5 rounded mr-1" style={{ backgroundColor: "#a1a1aa" }} /> SPY</span>
        </div>
        <div className="flex gap-2">
          {data.map((d) => (
            <div key={d.date} className="flex-1 min-w-[60px] text-center">
              {/* Simple bar representation */}
              <div className="h-24 flex items-end justify-center gap-0.5 mb-1">
                <Bar value={parseFloat(d.portfolio)} color="#d4a832" />
                <Bar value={parseFloat(d.universe)} color="#71717a" />
                <Bar value={parseFloat(d.spy)} color="#a1a1aa" />
              </div>
              <div className="text-[9px] font-mono" style={{ color: "var(--color-text-muted)" }}>
                {d.date.slice(5)}
              </div>
              {d.picks === 0 && (
                <div className="text-[8px]" style={{ color: "#eab308" }}>0 picks</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Bar({ value, color }: { value: number; color: string }) {
  const height = Math.max(2, Math.min(88, Math.abs(value) * 1.5));
  const isNeg = value < 0;
  return (
    <div className="w-3 rounded-sm transition-all duration-300"
         style={{
           height: `${height}px`,
           backgroundColor: color,
           opacity: 0.8,
           marginTop: isNeg ? "auto" : undefined,
           transform: isNeg ? "translateY(0)" : undefined,
         }}
         title={`${value}%`}
    />
  );
}

/* ── Quarterly Table ── */

function QuarterlyTable({ quarters }: { quarters: any[] }) {
  return (
    <div className="mb-8">
      <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
        Quarterly Breakdown
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--color-surface-3)" }}>
              {["#", "Period", "Picks", "Portfolio", "Universe", "SPY", "Excess"].map((h) => (
                <th key={h} className="text-[10px] font-medium uppercase tracking-[0.06em] py-2.5 px-2 text-right first:text-left"
                    style={{ color: "var(--color-text-muted)" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {quarters.map((q, i) => {
              const excess = q.excess_return;
              const exColor = excess > 0 ? "#22c55e" : excess < 0 ? "#ef4444" : "var(--color-text-secondary)";
              return (
                <tr key={q.date} className="border-b" style={{ borderColor: "rgba(39,39,42,0.5)" }}>
                  <td className="font-mono text-[12px] py-2 px-2" style={{ color: "var(--color-text-muted)" }}>{i + 1}</td>
                  <td className="font-mono text-[12px] py-2 px-2">{q.date}</td>
                  <td className="font-mono text-[12px] py-2 px-2 text-right"
                      style={{ color: q.num_picks === 0 ? "#eab308" : "var(--color-text-primary)" }}>
                    {q.num_picks}
                  </td>
                  <td className="font-mono text-[12px] py-2 px-2 text-right"
                      style={{ color: q.portfolio_return >= 0 ? "#22c55e" : "#ef4444" }}>
                    {q.portfolio_return >= 0 ? "+" : ""}{q.portfolio_return.toFixed(1)}%
                  </td>
                  <td className="font-mono text-[12px] py-2 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                    {q.universe_return >= 0 ? "+" : ""}{q.universe_return.toFixed(1)}%
                  </td>
                  <td className="font-mono text-[12px] py-2 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                    {q.spy_return >= 0 ? "+" : ""}{q.spy_return.toFixed(1)}%
                  </td>
                  <td className="font-mono text-[12px] py-2 px-2 text-right font-medium" style={{ color: exColor }}>
                    {excess >= 0 ? "+" : ""}{excess.toFixed(1)}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Investigation Summary ── */

function InvestigationSummary() {
  const findings = [
    { question: "Do conviction buys outperform?", signal: "MIXED", color: "#eab308",
      detail: "CB beat AVOID in 6/11 quarters. Average spread: -0.8%. Directional but not reliable per-quarter." },
    { question: "Does the momentum gate catch falling knives?", signal: "YES", color: "#22c55e",
      detail: "98 victims averaged +2.6% vs CB's +4.5%. Gate removed underperformers in 7/10 quarters. The screener's most validated component." },
    { question: "Does the F-Score gate help?", signal: "NEUTRAL", color: "#71717a",
      detail: "17 victims averaged +2.7% vs CB +4.5%. Gate fires rarely (0-4/quarter). Kept as cheap insurance." },
    { question: "Do confidence levels predict returns?", signal: "IN AGGREGATE", color: "#3b82f6",
      detail: "HIGH +6.7% > MOD +5.4% > LOW +3.3% in aggregate. But monotonic in only 1/11 quarters." },
    { question: "Are VALUE TRAPs actually traps?", signal: "YES", color: "#22c55e",
      detail: "Underperform CB in 7/11 quarters. Fail during commodity booms (Q4 2025: VT +26.6% vs CB +3.6%)." },
    { question: "Is this stock selection or sector rotation?", signal: "SECTOR", color: "#f97316",
      detail: "Sector-neutralized alpha: +0.1%. The screener tilts toward cheap, quality sectors — not individual stock picking." },
    { question: "Does conviction ordering predict returns within CB?", signal: "NO", color: "#ef4444",
      detail: "Kendall τ = -0.038. Higher conviction scores do not predict higher returns. Ranking is not predictive." },
    { question: "Are wins bigger than losses?", signal: "NO", color: "#ef4444",
      detail: "Win/loss ratio: 1.05× at 52% hit rate. No meaningful asymmetry." },
  ];

  return (
    <div>
      <h2 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-1" style={{ color: "var(--color-text-muted)" }}>
        Component Investigation
      </h2>
      <p className="text-[12px] mb-4" style={{ color: "var(--color-text-secondary)" }}>
        12 quarters analyzed. All findings are directional hypotheses (n&lt;30).
      </p>
      <div className="space-y-2">
        {findings.map((f) => (
          <div key={f.question} className="rounded-lg p-4"
               style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
            <div className="flex items-start justify-between mb-2">
              <div className="text-[13px] font-medium" style={{ color: "var(--color-text-primary)" }}>
                "{f.question}"
              </div>
              <span className="text-[10px] font-mono font-medium rounded-full px-2 py-0.5 ml-3 shrink-0"
                    style={{ backgroundColor: `${f.color}20`, color: f.color }}>
                {f.signal}
              </span>
            </div>
            <p className="text-[12px]" style={{ color: "var(--color-text-secondary)" }}>
              {f.detail}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

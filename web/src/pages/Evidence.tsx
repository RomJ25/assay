import { useState, useMemo, Fragment } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceDot, Label } from "recharts";
import { useBacktestData, type BacktestQuarter } from "../hooks/useBacktestData";

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

      {/* Limitations */}
      <div className="rounded-lg p-4 mb-8" style={{ backgroundColor: "#eab30808", border: "1px solid #eab30820" }}>
        <div className="text-[11px] uppercase tracking-[0.06em] mb-2 font-medium" style={{ color: "#eab308" }}>
          Known Limitations
        </div>
        <ul className="text-[12px] space-y-1" style={{ color: "var(--color-text-secondary)" }}>
          <li>Survivorship bias: uses current S&P 500 list (est. 2-5% CAGR overstatement)</li>
          <li>Sample size: {data.quarters.length} quarters (below 30-period minimum for significance)</li>
          <li>Data: Yahoo Finance (may include retroactive restatements)</li>
        </ul>
      </div>

      <PerformanceSummary quarters={data.quarters} />
      <CumulativeChart quarters={data.quarters} />
      <QuarterlyTable quarters={data.quarters} picks={data.picks} />
      <InvestigationSummary />
    </div>
  );
}

/* ── Performance Summary ── */

function PerformanceSummary({ quarters }: { quarters: BacktestQuarter[] }) {
  const stats = useMemo(() => {
    let portVal = 1, univVal = 1, spyVal = 1;
    let maxPort = 1, maxDD = 0;

    for (const q of quarters) {
      portVal *= (1 + q.portfolio_return / 100);
      univVal *= (1 + q.universe_return / 100);
      spyVal *= (1 + q.spy_return / 100);
      if (portVal > maxPort) maxPort = portVal;
      const dd = (maxPort - portVal) / maxPort;
      if (dd > maxDD) maxDD = dd;
    }

    const years = quarters.length / 4;
    const cagr = (pv: number) => years > 0 && pv > 0 ? pv ** (1 / years) - 1 : 0;

    return {
      totalReturn: portVal - 1, univReturn: univVal - 1, spyReturn: spyVal - 1,
      cagr: cagr(portVal), univCagr: cagr(univVal), spyCagr: cagr(spyVal),
      maxDD: -maxDD, selectionAlpha: cagr(portVal) - cagr(univVal), quarters: quarters.length,
    };
  }, [quarters]);

  return (
    <div className="mb-8">
      <SectionLabel>Performance Summary</SectionLabel>
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Portfolio", cagr: stats.cagr, total: stats.totalReturn },
          { label: "Universe (EW)", cagr: stats.univCagr, total: stats.univReturn },
          { label: "S&P 500 (SPY)", cagr: stats.spyCagr, total: stats.spyReturn },
        ].map((c) => (
          <div key={c.label} className="rounded-lg p-4" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
            <div className="text-[10px] uppercase tracking-[0.06em] mb-2" style={{ color: "var(--color-text-muted)" }}>{c.label}</div>
            <div className="font-mono text-2xl font-semibold mb-1" style={{ color: c.cagr >= 0 ? "#22c55e" : "#ef4444" }}>
              {(c.cagr * 100).toFixed(1)}%
            </div>
            <div className="text-[11px]" style={{ color: "var(--color-text-secondary)" }}>CAGR · Total: {(c.total * 100).toFixed(1)}%</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-3 mt-3">
        <SmallCard label="Selection Alpha" value={`${(stats.selectionAlpha * 100).toFixed(1)}%`}
                   color={stats.selectionAlpha >= 0 ? "#22c55e" : "#ef4444"} sub="Portfolio - Universe CAGR" />
        <SmallCard label="Max Drawdown" value={`${(stats.maxDD * 100).toFixed(1)}%`} color="#ef4444" sub="Peak-to-trough" />
        <SmallCard label="Quarters" value={`${stats.quarters}`}
                   color="var(--color-text-primary)" sub={stats.quarters < 30 ? "Below 30-quarter minimum" : ""} />
      </div>
    </div>
  );
}

/* ── Recharts Cumulative Line Chart ── */

function CumulativeChart({ quarters }: { quarters: BacktestQuarter[] }) {
  const chartData = useMemo(() => {
    let portVal = 100, univVal = 100, spyVal = 100;
    const points = [{ date: "Start", portfolio: 100, universe: 100, spy: 100, picks: -1 }];
    for (const q of quarters) {
      portVal *= (1 + q.portfolio_return / 100);
      univVal *= (1 + q.universe_return / 100);
      spyVal *= (1 + q.spy_return / 100);
      points.push({
        date: q.date.slice(2), // "22-03-31"
        portfolio: Math.round(portVal * 10) / 10,
        universe: Math.round(univVal * 10) / 10,
        spy: Math.round(spyVal * 10) / 10,
        picks: q.num_picks,
      });
    }
    return points;
  }, [quarters]);

  return (
    <div className="rounded-lg p-5 mb-8" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <SectionLabel>Cumulative Returns (Growth of $100)</SectionLabel>
      <div className="flex gap-6 text-[11px] mb-4" style={{ color: "var(--color-text-secondary)" }}>
        <span><span className="inline-block w-3 h-0.5 rounded mr-1.5" style={{ backgroundColor: "#d4a832" }} />Portfolio</span>
        <span><span className="inline-block w-3 h-0.5 rounded mr-1.5" style={{ backgroundColor: "#71717a" }} />Universe</span>
        <span><span className="inline-block w-3 h-0.5 rounded mr-1.5 opacity-60" style={{ backgroundColor: "#a1a1aa" }} />SPY</span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={{ stroke: "#27272a" }} />
          <YAxis tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false} axisLine={false}
                 tickFormatter={(v: number) => `$${v}`} domain={["auto", "auto"]} />
          <ReferenceLine y={100} stroke="#27272a" strokeDasharray="3 3" />
          <Tooltip
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px", fontSize: "12px" }}
            labelStyle={{ color: "#a1a1aa", marginBottom: "4px" }}
            formatter={(value: any, name: any) => [`$${Number(value).toFixed(1)}`, name === "portfolio" ? "Portfolio" : name === "universe" ? "Universe" : "SPY"]}
          />
          <Line type="monotone" dataKey="portfolio" stroke="#d4a832" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="universe" stroke="#71717a" strokeWidth={1.5} dot={false} />
          <Line type="monotone" dataKey="spy" stroke="#a1a1aa" strokeWidth={1} strokeDasharray="4 4" dot={false} />
          {/* Annotated events */}
          {chartData.map((d, i) => {
            if (d.picks === 0 && i > 0) {
              return <ReferenceDot key={`zero-${i}`} x={d.date} y={d.portfolio} r={3} fill="#eab308" stroke="none" />;
            }
            return null;
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ── Quarterly Table with Drill-Down ── */

function QuarterlyTable({ quarters, picks }: { quarters: BacktestQuarter[]; picks: any[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="mb-8">
      <SectionLabel>Quarterly Breakdown</SectionLabel>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--color-surface-3)" }}>
              {["#", "Period", "Picks", "Portfolio", "Universe", "SPY", "Excess"].map((h) => (
                <th key={h} className="text-[10px] font-medium uppercase tracking-[0.06em] py-2.5 px-2 text-right first:text-left"
                    style={{ color: "var(--color-text-muted)" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {quarters.map((q, i) => {
              const isExpanded = expanded === q.date;
              const quarterPicks = picks.filter((p) => p.quarter === q.date);
              const excess = q.excess_return;
              const exColor = excess > 0 ? "#22c55e" : excess < 0 ? "#ef4444" : "var(--color-text-secondary)";

              return (
                <Fragment key={q.date}>
                  <tr className="border-b cursor-pointer transition-colors duration-100"
                      style={{ borderColor: "rgba(39,39,42,0.5)", backgroundColor: isExpanded ? "var(--color-surface-1)" : "transparent" }}
                      onClick={() => setExpanded(isExpanded ? null : q.date)}
                      onMouseEnter={(e) => { if (!isExpanded) e.currentTarget.style.backgroundColor = "var(--color-surface-1)"; }}
                      onMouseLeave={(e) => { if (!isExpanded) e.currentTarget.style.backgroundColor = "transparent"; }}>
                    <td className="font-mono text-[12px] py-2.5 px-2" style={{ color: "var(--color-text-muted)" }}>{i + 1}</td>
                    <td className="font-mono text-[12px] py-2.5 px-2">
                      {isExpanded ? "▾" : "▸"} {q.date}
                    </td>
                    <td className="font-mono text-[12px] py-2.5 px-2 text-right"
                        style={{ color: q.num_picks === 0 ? "#eab308" : "var(--color-text-primary)" }}>
                      {q.num_picks}
                    </td>
                    <td className="font-mono text-[12px] py-2.5 px-2 text-right"
                        style={{ color: q.portfolio_return >= 0 ? "#22c55e" : "#ef4444" }}>
                      {q.portfolio_return >= 0 ? "+" : ""}{q.portfolio_return.toFixed(1)}%
                    </td>
                    <td className="font-mono text-[12px] py-2.5 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                      {q.universe_return >= 0 ? "+" : ""}{q.universe_return.toFixed(1)}%
                    </td>
                    <td className="font-mono text-[12px] py-2.5 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                      {q.spy_return >= 0 ? "+" : ""}{q.spy_return.toFixed(1)}%
                    </td>
                    <td className="font-mono text-[12px] py-2.5 px-2 text-right font-medium" style={{ color: exColor }}>
                      {excess >= 0 ? "+" : ""}{excess.toFixed(1)}%
                    </td>
                  </tr>

                  {/* Expanded: show picks for this quarter */}
                  {isExpanded && quarterPicks.length > 0 && (
                    <tr>
                      <td colSpan={7} className="px-2 py-3" style={{ backgroundColor: "var(--color-surface-1)" }}>
                        <div className="pl-8 pr-4">
                          <div className="text-[10px] uppercase tracking-[0.06em] mb-2" style={{ color: "var(--color-text-muted)" }}>
                            Picks for {q.date}
                          </div>
                          <div className="grid grid-cols-2 gap-x-6 gap-y-1">
                            {quarterPicks.map((p: any) => (
                              <div key={p.ticker} className="flex items-center gap-2 py-0.5">
                                <span className="font-mono text-[12px] font-semibold w-12">{p.ticker}</span>
                                <span className="text-[11px] flex-1 truncate" style={{ color: "var(--color-text-secondary)" }}>{p.sector}</span>
                                <span className="font-mono text-[10px]" style={{ color: "var(--color-text-muted)" }}>
                                  V={Math.round(p.value_score)} Q={Math.round(p.quality_score)} F={p.piotroski_f}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                  {isExpanded && quarterPicks.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-2 py-3 text-center text-[12px] italic"
                          style={{ backgroundColor: "var(--color-surface-1)", color: "#eab308" }}>
                        Zero picks this quarter — portfolio held cash
                      </td>
                    </tr>
                  )}
                </Fragment>
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
      detail: "98 victims averaged +2.6% vs CB's +4.5%. Gate removed underperformers in 7/10 quarters." },
    { question: "Does the F-Score gate help?", signal: "NEUTRAL", color: "#71717a",
      detail: "17 victims averaged +2.7% vs CB +4.5%. Gate fires rarely (0-4/quarter). Kept as cheap insurance." },
    { question: "Do confidence levels predict returns?", signal: "IN AGGREGATE", color: "#3b82f6",
      detail: "HIGH +6.7% > MOD +5.4% > LOW +3.3% in aggregate. But monotonic in only 1/11 quarters." },
    { question: "Are VALUE TRAPs actually traps?", signal: "YES", color: "#22c55e",
      detail: "Underperform CB in 7/11 quarters. Fail during commodity booms." },
    { question: "Is this stock selection or sector rotation?", signal: "IMPROVED", color: "#3b82f6",
      detail: "Under quarterly rebalance: +0.1% sector-neutral alpha. Under selective sell strategy: +0.5%. Holding winners improves stock selection." },
    { question: "Does conviction ordering predict returns?", signal: "NO", color: "#ef4444",
      detail: "Kendall τ = -0.038. Higher conviction scores do not predict higher returns within CB." },
    { question: "Are wins bigger than losses?", signal: "WITH STRATEGY", color: "#22c55e",
      detail: "Under quarterly rebalance: 1.05× (no asymmetry). Under selective sell: 1.28× (meaningful). Holding winners creates asymmetry." },
  ];

  return (
    <div>
      <SectionLabel>Component Investigation</SectionLabel>
      <p className="text-[12px] mb-4" style={{ color: "var(--color-text-secondary)" }}>
        12 quarters analyzed. All findings are directional hypotheses (n&lt;30).
      </p>
      <div className="grid grid-cols-2 gap-2">
        {findings.map((f) => (
          <div key={f.question} className="rounded-lg p-4"
               style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
            <div className="flex items-start justify-between mb-2">
              <div className="text-[13px] font-medium" style={{ color: "var(--color-text-primary)" }}>
                "{f.question}"
              </div>
              <span className="text-[10px] font-mono font-medium rounded-full px-2 py-0.5 ml-2 shrink-0"
                    style={{ backgroundColor: `${f.color}20`, color: f.color }}>
                {f.signal}
              </span>
            </div>
            <p className="text-[11px] leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>{f.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Shared ── */

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
      {children}
    </h3>
  );
}

function SmallCard({ label, value, color, sub }: { label: string; value: string; color: string; sub: string }) {
  return (
    <div className="rounded-lg p-4" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <div className="text-[10px] uppercase tracking-[0.06em] mb-2" style={{ color: "var(--color-text-muted)" }}>{label}</div>
      <div className="font-mono text-xl font-semibold mb-1" style={{ color }}>{value}</div>
      <div className="text-[10px]" style={{ color: "var(--color-text-secondary)" }}>{sub}</div>
    </div>
  );
}

// Fragment imported at top of file

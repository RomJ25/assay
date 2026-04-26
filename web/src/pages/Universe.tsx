import { useState, useMemo } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { useScreenData } from "../hooks/useScreenData";
import { StockSheet } from "../components/stock/StockSheet";
import { classificationColors } from "../lib/colors";
import { useCountUp } from "../hooks/useCountUp";
import type { ScreenStock, Classification } from "../lib/types";

const MATRIX: Classification[][] = [
  ["RESEARCH CANDIDATE", "WATCH LIST", "VALUE TRAP"],
  ["QUALITY GROWTH PREMIUM", "HOLD", "AVOID"],
  ["OVERVALUED QUALITY", "OVERVALUED", "AVOID"],
];

const SHORT_LABELS: Record<string, string> = {
  "RESEARCH CANDIDATE": "Conviction Buy",
  "QUALITY GROWTH PREMIUM": "Quality Growth",
  "WATCH LIST": "Watch List",
  HOLD: "Hold",
  "OVERVALUED QUALITY": "Overvalued Quality",
  OVERVALUED: "Overvalued",
  "VALUE TRAP": "Value Trap",
  AVOID: "Avoid",
};

export function Universe() {
  const { data, loading, error } = useScreenData();
  const [selectedCell, setSelectedCell] = useState<Classification | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const bucketMap = useMemo(() => {
    if (!data) return new Map<string, ScreenStock[]>();
    const map = new Map<string, ScreenStock[]>();
    for (const s of data.stocks) {
      const list = map.get(s.classification) || [];
      list.push(s);
      map.set(s.classification, list);
    }
    // Sort each bucket by conviction
    for (const [, list] of map) {
      list.sort((a, b) => (b.conviction_score || 0) - (a.conviction_score || 0));
    }
    return map;
  }, [data]);

  const filteredStocks = useMemo(() => {
    if (!data) return [];
    let stocks = selectedCell
      ? (bucketMap.get(selectedCell) || [])
      : data.stocks;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      stocks = stocks.filter((s) => s.ticker.toLowerCase().includes(q) || s.company.toLowerCase().includes(q));
    }
    return stocks.sort((a, b) => (b.conviction_score || 0) - (a.conviction_score || 0));
  }, [data, selectedCell, searchQuery, bucketMap]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-48 h-1 rounded-full overflow-hidden" style={{ backgroundColor: "var(--color-surface-2)" }}>
          <div className="h-full rounded-full animate-pulse" style={{ backgroundColor: "var(--color-cb)", width: "40%" }} />
        </div>
        <p className="mt-4 text-[13px]" style={{ color: "var(--color-text-muted)" }}>Loading universe data...</p>
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-[13px]" style={{ color: "#ef4444" }}>{error || "No data"}</p>
      </div>
    );
  }

  const selectedStock = selectedTicker ? data.stocks.find((s) => s.ticker === selectedTicker) : null;

  return (
    <div className="px-8 py-10">
      <h1 className="text-xl font-semibold mb-1">Universe</h1>
      <p className="text-[13px] mb-8" style={{ color: "var(--color-text-secondary)" }}>
        All {data.screened} screened stocks on the classification matrix.
        {selectedCell && (
          <button className="ml-2 underline hover:opacity-80" onClick={() => setSelectedCell(null)}>
            Clear filter
          </button>
        )}
      </p>

      {/* 3×3 Classification Matrix */}
      <div className="mb-10">
        {/* Axis labels */}
        <div className="flex items-center mb-2">
          <div className="w-24" />
          <div className="flex-1 flex justify-between text-[10px] tracking-wide px-1"
               style={{ color: "var(--color-text-muted)" }}>
            <span>← Quality High (≥70)</span>
            <span>Quality Mid (40-70)</span>
            <span>Quality Low (&lt;40) →</span>
          </div>
        </div>

        <div className="flex gap-0">
          {/* Y-axis labels */}
          <div className="w-24 flex flex-col justify-around pr-2 text-right text-[10px] tracking-wide"
               style={{ color: "var(--color-text-muted)" }}>
            <span>Value High<br />(≥70)</span>
            <span>Value Mid<br />(40-70)</span>
            <span>Value Low<br />(&lt;40)</span>
          </div>

          {/* Grid */}
          <div className="flex-1 grid grid-rows-3 gap-1.5">
            {MATRIX.map((row, ri) => (
              <div key={ri} className="grid grid-cols-3 gap-1.5">
                {row.map((cl, ci) => {
                  // Handle AVOID appearing twice
                  const key = `${ri}-${ci}`;
                  // AVOID appears in two cells: v_mid+q_low (row 1, col 2) and v_low+q_low (row 2, col 2)
                  let cellStocks: ScreenStock[];
                  if (cl === "AVOID" && ri === 1) {
                    cellStocks = (bucketMap.get("AVOID") || []).filter((s) => s.value_score >= 40);
                  } else if (cl === "AVOID" && ri === 2) {
                    cellStocks = (bucketMap.get("AVOID") || []).filter((s) => s.value_score < 40);
                  } else {
                    cellStocks = bucketMap.get(cl) || [];
                  }
                  const displayCount = cellStocks.length;
                  const color = classificationColors[cl];
                  const isSelected = selectedCell === cl;
                  const cellDelay = (ri * 3 + ci) * 40;

                  return (
                    <MatrixCell
                      key={key}
                      count={displayCount}
                      color={color}
                      label={SHORT_LABELS[cl]}
                      isSelected={isSelected}
                      dimmed={selectedCell !== null && !isSelected}
                      delay={cellDelay}
                      onClick={() => setSelectedCell(isSelected ? null : cl)}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-between mt-2 text-[10px] italic pl-24"
             style={{ color: "var(--color-text-muted)" }}>
          <span>← Cheap + High Quality = best</span>
          <span>Expensive + Low Quality = worst →</span>
        </div>
      </div>

      {/* V vs Q Scatter Plot */}
      <VQScatter stocks={data.stocks} onSelectStock={setSelectedTicker} />

      {/* Search + Stock Table */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by ticker or company..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full max-w-sm rounded-md px-3 py-2 text-[13px] outline-none transition-colors"
          style={{
            backgroundColor: "var(--color-surface-1)",
            border: "1px solid var(--color-border)",
            color: "var(--color-text-primary)",
          }}
        />
      </div>

      <div className="text-[11px] uppercase tracking-[0.06em] mb-3" style={{ color: "var(--color-text-muted)" }}>
        {selectedCell ? `${SHORT_LABELS[selectedCell]} — ${filteredStocks.length} stocks` : `All ${filteredStocks.length} stocks`}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--color-surface-3)" }}>
              {["Ticker", "Company", "Classification", "V", "Q", "Conv", "F", "EY%", "Sector"].map((h) => (
                <th key={h} className={`text-[10px] font-medium uppercase tracking-[0.06em] py-2.5 px-2 text-left ${
                  ["V", "Q", "Conv", "F", "EY%"].includes(h) ? "text-right" : ""
                }`} style={{ color: "var(--color-text-muted)" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredStocks.slice(0, 100).map((s) => {
              const clColor = classificationColors[s.classification] || "#71717a";
              return (
                <tr key={s.ticker}
                    className="border-b cursor-pointer transition-colors duration-100"
                    style={{ borderColor: "rgba(39,39,42,0.5)" }}
                    onClick={() => setSelectedTicker(s.ticker)}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--color-surface-1)")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}>
                  <td className="font-mono text-sm font-semibold py-2.5 px-2">{s.ticker}</td>
                  <td className="text-[13px] py-2.5 px-2 truncate max-w-[200px]" style={{ color: "var(--color-text-secondary)" }}>{s.company}</td>
                  <td className="py-2.5 px-2">
                    <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium"
                          style={{ backgroundColor: `${clColor}26`, color: clColor }}>
                      {SHORT_LABELS[s.classification]}
                    </span>
                  </td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right">{Math.round(s.value_score)}</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right">{Math.round(s.quality_score)}</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right font-medium">{s.conviction_score.toFixed(1)}</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>{s.piotroski_f}/9</td>
                  <td className="font-mono text-[13px] py-2.5 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                    {s.earnings_yield != null ? `${s.earnings_yield.toFixed(1)}%` : "—"}
                  </td>
                  <td className="text-[11px] uppercase tracking-wide py-2.5 px-2" style={{ color: "var(--color-text-muted)" }}>{s.sector}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {filteredStocks.length > 100 && (
          <p className="text-[12px] py-4 text-center" style={{ color: "var(--color-text-muted)" }}>
            Showing 100 of {filteredStocks.length} stocks
          </p>
        )}
      </div>

      {/* Stock Deep Dive */}
      {selectedStock && (
        <StockSheet stock={selectedStock} allStocks={data.stocks} onClose={() => setSelectedTicker(null)} />
      )}
    </div>
  );
}

/* ── Matrix cell with count-up + selection focus ── */

function MatrixCell({ count, color, label, isSelected, dimmed, delay, onClick }: {
  count: number; color: string; label: string;
  isSelected: boolean; dimmed: boolean; delay: number; onClick: () => void;
}) {
  const animated = useCountUp(count, 600, delay);
  return (
    <button
      className="rounded-lg p-3 text-left transition-all duration-200 hover:scale-[1.01] anim-fade-scale"
      style={{
        backgroundColor: isSelected ? `${color}1a` : `${color}0a`,
        border: `1px solid ${isSelected ? `${color}40` : `${color}20`}`,
        opacity: dimmed ? 0.4 : 1,
        animationDelay: `${delay}ms`,
      }}
      onClick={onClick}
    >
      <div className="text-[11px] font-medium mb-1" style={{ color }}>
        {label}
      </div>
      <div className="font-mono text-lg font-semibold tabular-nums" style={{ color: "var(--color-text-primary)" }}>
        {Math.round(animated)}
      </div>
      <div className="text-[10px]" style={{ color: "var(--color-text-muted)" }}>
        stocks
      </div>
    </button>
  );
}

/* ── V vs Q Scatter Plot ── */

function VQScatter({ stocks, onSelectStock }: { stocks: ScreenStock[]; onSelectStock: (t: string) => void }) {
  const [showScatter, setShowScatter] = useState(false);

  // Group stocks by classification for colored dots
  const scatterData = useMemo(() => {
    const groups: Record<string, { x: number; y: number; ticker: string; company: string; cl: string }[]> = {};
    for (const s of stocks) {
      const cl = s.classification;
      if (!groups[cl]) groups[cl] = [];
      groups[cl].push({
        x: s.value_score,
        y: s.quality_score,
        ticker: s.ticker,
        company: s.company,
        cl,
      });
    }
    return groups;
  }, [stocks]);

  if (!showScatter) {
    return (
      <div className="mb-8 text-center">
        <button className="text-[11px] rounded-md px-3 py-1.5 transition-colors hover:opacity-80"
                style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)", color: "var(--color-text-secondary)" }}
                onClick={() => setShowScatter(true)}>
          Show V vs Q Scatter Plot
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-lg p-5 mb-8" style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-[11px] font-medium uppercase tracking-[0.06em]" style={{ color: "var(--color-text-muted)" }}>
            Value Score vs Quality Score — All {stocks.length} Stocks
          </h3>
          <p className="text-[10px] mt-1" style={{ color: "var(--color-text-muted)" }}>
            Each dot is a stock. Dashed lines at 40 and 70 mark the classification thresholds.
          </p>
        </div>
        <button className="text-[11px] hover:opacity-80" style={{ color: "var(--color-text-muted)" }}
                onClick={() => setShowScatter(false)}>Hide</button>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mb-4 text-[10px]">
        {(Object.keys(SHORT_LABELS) as Classification[]).map((cl) => (
          <span key={cl} className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: classificationColors[cl] }} />
            {SHORT_LABELS[cl]}
          </span>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
          <XAxis type="number" dataKey="x" domain={[0, 100]} name="Value"
                 tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false}
                 axisLine={{ stroke: "#27272a" }}
                 label={{ value: "Value Score →", position: "bottom", offset: 10, fontSize: 11, fill: "#71717a" }} />
          <YAxis type="number" dataKey="y" domain={[0, 100]} name="Quality"
                 tick={{ fontSize: 10, fill: "#71717a" }} tickLine={false}
                 axisLine={{ stroke: "#27272a" }}
                 label={{ value: "Quality Score →", angle: -90, position: "insideLeft", offset: 0, fontSize: 11, fill: "#71717a" }} />

          {/* Threshold lines */}
          <ReferenceLine x={40} stroke="#27272a" strokeDasharray="4 4" />
          <ReferenceLine x={70} stroke="#3f3f46" strokeDasharray="4 4" />
          <ReferenceLine y={40} stroke="#27272a" strokeDasharray="4 4" />
          <ReferenceLine y={70} stroke="#3f3f46" strokeDasharray="4 4" />

          <Tooltip
            cursor={false}
            contentStyle={{ backgroundColor: "#18181b", border: "1px solid #27272a", borderRadius: "8px", fontSize: "12px" }}
            formatter={(_: any, __: any, props: any) => {
              const p = props.payload;
              return [`V=${Math.round(p.x)} Q=${Math.round(p.y)}`, `${p.ticker} (${p.cl})`];
            }}
          />

          {/* Plot each classification group with its color */}
          {Object.entries(scatterData).map(([cl, points]) => (
            <Scatter
              key={cl}
              data={points}
              fill={classificationColors[cl as Classification] || "#71717a"}
              fillOpacity={0.7}
              r={3}
              cursor="pointer"
              onClick={(data: any) => onSelectStock(data.ticker)}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

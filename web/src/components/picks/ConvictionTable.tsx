import { useState, useMemo } from "react";
import type { ScreenStock } from "../../lib/types";
import { classificationColors, confidenceColors, confidenceIcons, scoreColor, scoreBgOpacity } from "../../lib/colors";
import { fmtScore, fmtPercent, fmtPrice, fmtFScore, fmtAnalyst } from "../../lib/format";
import { CompareView } from "./CompareView";
import { StockLogo } from "../ui/StockLogo";

interface Props {
  stocks: ScreenStock[];
  onSelectStock: (ticker: string) => void;
}

type SortKey = "conviction_score" | "value_score" | "quality_score" | "piotroski_f" | "earnings_yield" | "price" | "ticker";
type SortDir = "asc" | "desc";

export function ConvictionTable({ stocks, onSelectStock }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("conviction_score");
  const [compareMode, setCompareMode] = useState(false);
  const [compareSet, setCompareSet] = useState<Set<string>>(new Set());
  const [showCompare, setShowCompare] = useState(false);
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const cbPicks = useMemo(
    () => stocks.filter((s) => s.classification === "RESEARCH CANDIDATE"),
    [stocks]
  );

  const sorted = useMemo(() => {
    const list = [...cbPicks];
    list.sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (typeof av === "string" && typeof bv === "string") {
        return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
      }
      return sortDir === "asc" ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
    return list;
  }, [cbPicks, sortKey, sortDir]);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  if (cbPicks.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 px-8">
        <p className="text-lg mb-2" style={{ color: "var(--color-text-secondary)" }}>
          No conviction buys this screen.
        </p>
        <p className="text-[13px]" style={{ color: "var(--color-text-muted)" }}>
          The screener found no stocks where value, quality, and momentum all align.
        </p>
      </div>
    );
  }

  const sortIndicator = (key: SortKey) => {
    if (sortKey !== key) return "";
    return sortDir === "asc" ? " ↑" : " ↓";
  };

  function exportCSV() {
    const headers = ["Rank", "Ticker", "Company", "Sector", "Price", "Conv", "Confidence", "V", "Q", "F", "EY%", "Analyst Target"];
    const rows = sorted.map((s, i) => [
      i + 1, s.ticker, s.company, s.sector, s.price.toFixed(2),
      s.conviction_score.toFixed(1), s.confidence || "",
      Math.round(s.value_score), Math.round(s.quality_score),
      s.piotroski_f, s.earnings_yield?.toFixed(1) ?? "",
      s.analyst_target?.toFixed(0) ?? "",
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `assay_conviction_buys.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="px-4 sm:px-8 pb-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-[11px] font-medium uppercase tracking-[0.06em]"
              style={{ color: "var(--color-text-muted)" }}>
            All {cbPicks.length} Research Candidates
          </h2>
          <p className="text-[11px] mt-1" style={{ color: "var(--color-text-muted)" }}>
            Ranking does not predict returns within RC (Kendall τ ≈ −0.04, n=12 quarters). Treat as research input, not a forecast.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {compareMode && compareSet.size >= 2 && (
            <button
              className="text-[11px] rounded-md px-2.5 py-1 font-medium transition-colors"
              style={{ backgroundColor: "var(--color-cb)", color: "#000" }}
              onClick={() => setShowCompare(true)}
            >
              Compare {compareSet.size} →
            </button>
          )}
          <button
            className="text-[11px] rounded-md px-2.5 py-1 transition-colors hover:opacity-80"
            style={{
              backgroundColor: compareMode ? "var(--color-surface-2)" : "var(--color-surface-1)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text-secondary)",
            }}
            onClick={() => { setCompareMode(!compareMode); setCompareSet(new Set()); }}
          >
            {compareMode ? "Cancel" : "Compare"}
          </button>
          <button
            className="text-[11px] rounded-md px-2.5 py-1 transition-colors hover:opacity-80"
            style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)", color: "var(--color-text-secondary)" }}
            onClick={exportCSV}
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Compare view overlay */}
      {showCompare && compareSet.size >= 2 && (
        <CompareView
          stocks={sorted.filter((s) => compareSet.has(s.ticker))}
          onClose={() => { setShowCompare(false); setCompareMode(false); setCompareSet(new Set()); }}
        />
      )}

      {/* Mobile card view (< 768px) */}
      <div className="block sm:hidden space-y-2 mb-4">
        {sorted.map((s, i) => {
          const confColor = s.confidence ? confidenceColors[s.confidence] : null;
          return (
            <div
              key={s.ticker}
              className="rounded-lg p-3 cursor-pointer transition-colors duration-100 anim-fade-up"
              style={{
                backgroundColor: "var(--color-surface-1)",
                border: "1px solid var(--color-border)",
                animationDelay: `${1100 + Math.min(i, 20) * 20}ms`,
              }}
              onClick={() => onSelectStock(s.ticker)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm font-semibold">{s.ticker}</span>
                  <span className="text-[12px] truncate max-w-[140px]" style={{ color: "var(--color-text-secondary)" }}>{s.company}</span>
                </div>
                {s.confidence && (
                  <span className="text-[10px] rounded-full px-1.5 py-0.5 font-medium"
                        style={{ backgroundColor: `${confColor}26`, color: confColor! }}>
                    {confidenceIcons[s.confidence]} {s.confidence}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-lg font-semibold" style={{ color: scoreColor(s.conviction_score) }}>
                  {s.conviction_score.toFixed(1)}
                </span>
                <span className="font-mono text-[12px] rounded px-1 py-0.5"
                      style={{ backgroundColor: `${scoreColor(s.value_score)}0f` }}>
                  V {Math.round(s.value_score)}
                </span>
                <span className="font-mono text-[12px] rounded px-1 py-0.5"
                      style={{ backgroundColor: `${scoreColor(s.quality_score)}0f` }}>
                  Q {Math.round(s.quality_score)}
                </span>
                <span className="font-mono text-[11px]" style={{ color: "var(--color-text-muted)" }}>
                  F={s.piotroski_f}/9
                </span>
                <span className="ml-auto font-mono text-[12px]" style={{ color: "var(--color-text-secondary)" }}>
                  {fmtPrice(s.price)}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Desktop table view (≥ 768px) */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b" style={{ borderColor: "var(--color-surface-3)" }}>
              {[
                { key: null, label: "#", w: "w-10" },
                { key: "ticker" as SortKey, label: "Ticker", w: "w-20" },
                { key: null, label: "Company", w: "w-44" },
                { key: "price" as SortKey, label: "Price", w: "w-20", right: true },
                { key: "conviction_score" as SortKey, label: "Conv", w: "w-16", right: true },
                { key: null, label: "Conf", w: "w-16" },
                { key: "value_score" as SortKey, label: "V", w: "w-14", right: true },
                { key: "quality_score" as SortKey, label: "Q", w: "w-14", right: true },
                { key: "piotroski_f" as SortKey, label: "F", w: "w-12", right: true },
                { key: "earnings_yield" as SortKey, label: "EY%", w: "w-16", right: true },
                { key: null, label: "Sector", w: "w-28" },
                { key: null, label: "Analyst", w: "w-24", right: true },
              ].map((col, i) => (
                <th
                  key={i}
                  className={`text-[10px] font-medium uppercase tracking-[0.06em] py-2.5 px-2 ${
                    col.right ? "text-right" : "text-left"
                  } ${col.w} ${col.key ? "cursor-pointer hover:opacity-80 select-none" : ""}`}
                  style={{ color: "var(--color-text-muted)" }}
                  onClick={() => col.key && handleSort(col.key)}
                >
                  {col.label}{col.key ? sortIndicator(col.key) : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((s, i) => (
              <tr
                key={s.ticker}
                className="border-b cursor-pointer transition-colors duration-100 anim-fade-up"
                style={{
                  borderColor: "rgba(39, 39, 42, 0.5)",
                  animationDelay: `${1100 + Math.min(i, 20) * 20}ms`,
                  animationDuration: "220ms",
                }}
                onClick={() => {
                  if (compareMode) {
                    setCompareSet((prev) => {
                      const next = new Set(prev);
                      if (next.has(s.ticker)) next.delete(s.ticker);
                      else if (next.size < 4) next.add(s.ticker);
                      return next;
                    });
                  } else {
                    onSelectStock(s.ticker);
                  }
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--color-surface-1)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
              >
                {/* # or checkbox */}
                <td className="font-mono text-[13px] py-3 px-2 text-right" style={{ color: "var(--color-text-muted)" }}>
                  {compareMode ? (
                    <span className="inline-flex w-4 h-4 rounded border items-center justify-center text-[10px]"
                          style={{
                            borderColor: compareSet.has(s.ticker) ? "var(--color-cb)" : "var(--color-border)",
                            backgroundColor: compareSet.has(s.ticker) ? "var(--color-cb)" : "transparent",
                            color: compareSet.has(s.ticker) ? "#000" : "transparent",
                          }}>
                      ✓
                    </span>
                  ) : (
                    i + 1
                  )}
                </td>
                {/* Ticker + Logo */}
                <td className="py-3 px-2">
                  <div className="flex items-center gap-2">
                    <StockLogo ticker={s.ticker} company={s.company} size={20} />
                    <span className="font-mono text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                      {s.ticker}
                    </span>
                  </div>
                </td>
                {/* Company */}
                <td className="text-[13px] py-3 px-2 truncate max-w-[176px]" style={{ color: "var(--color-text-secondary)" }}>
                  {s.company}
                </td>
                {/* Price */}
                <td className="font-mono text-[13px] py-3 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                  {fmtPrice(s.price)}
                </td>
                {/* Conviction */}
                <td className="font-mono text-sm font-medium py-3 px-2 text-right" style={{ color: "var(--color-text-primary)" }}>
                  {fmtScore(s.conviction_score)}
                </td>
                {/* Confidence */}
                <td className="py-3 px-2">
                  {s.confidence && (
                    <span
                      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium"
                      style={{
                        backgroundColor: `${confidenceColors[s.confidence]}26`,
                        color: confidenceColors[s.confidence],
                      }}
                    >
                      {confidenceIcons[s.confidence]} {s.confidence}
                    </span>
                  )}
                </td>
                {/* Value Score */}
                <td className="py-3 px-2 text-right">
                  <span
                    className="font-mono text-[13px] rounded px-1.5 py-0.5"
                    style={{
                      backgroundColor: `${scoreColor(s.value_score)}${Math.round(scoreBgOpacity(s.value_score) * 255).toString(16).padStart(2, "0")}`,
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {Math.round(s.value_score)}
                  </span>
                </td>
                {/* Quality Score */}
                <td className="py-3 px-2 text-right">
                  <span
                    className="font-mono text-[13px] rounded px-1.5 py-0.5"
                    style={{
                      backgroundColor: `${scoreColor(s.quality_score)}${Math.round(scoreBgOpacity(s.quality_score) * 255).toString(16).padStart(2, "0")}`,
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {Math.round(s.quality_score)}
                  </span>
                </td>
                {/* F-Score */}
                <td className="font-mono text-[13px] py-3 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                  {fmtFScore(s.piotroski_f)}
                </td>
                {/* EY% */}
                <td className="font-mono text-[13px] py-3 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                  {s.earnings_yield != null ? `${s.earnings_yield.toFixed(1)}%` : "—"}
                </td>
                {/* Sector */}
                <td className="text-[11px] uppercase tracking-wide py-3 px-2 truncate max-w-[112px]"
                    style={{ color: "var(--color-text-muted)" }}>
                  {s.sector}
                </td>
                {/* Analyst */}
                <td className="font-mono text-[12px] py-3 px-2 text-right" style={{ color: "var(--color-text-secondary)" }}>
                  {fmtAnalyst(s.analyst_target, s.analyst_upside)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

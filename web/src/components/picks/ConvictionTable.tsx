import { useState, useMemo } from "react";
import type { ScreenStock } from "../../lib/types";
import { classificationColors, confidenceColors, confidenceIcons, scoreColor, scoreBgOpacity } from "../../lib/colors";
import { fmtScore, fmtPercent, fmtPrice, fmtFScore, fmtAnalyst } from "../../lib/format";

interface Props {
  stocks: ScreenStock[];
  onSelectStock: (ticker: string) => void;
}

type SortKey = "conviction_score" | "value_score" | "quality_score" | "piotroski_f" | "earnings_yield" | "price" | "ticker";
type SortDir = "asc" | "desc";

export function ConvictionTable({ stocks, onSelectStock }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("conviction_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const cbPicks = useMemo(
    () => stocks.filter((s) => s.classification === "CONVICTION BUY"),
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

  return (
    <div className="px-8 pb-8">
      <h2 className="text-[11px] font-medium uppercase tracking-[0.06em] mb-4"
          style={{ color: "var(--color-text-muted)" }}>
        All {cbPicks.length} Conviction Buys
      </h2>

      <div className="overflow-x-auto">
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
                className="border-b cursor-pointer transition-colors duration-100"
                style={{
                  borderColor: "rgba(39, 39, 42, 0.5)",
                }}
                onClick={() => onSelectStock(s.ticker)}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "var(--color-surface-1)")}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
              >
                {/* # */}
                <td className="font-mono text-[13px] py-3 px-2 text-right" style={{ color: "var(--color-text-muted)" }}>
                  {i + 1}
                </td>
                {/* Ticker */}
                <td className="font-mono text-sm font-semibold py-3 px-2" style={{ color: "var(--color-text-primary)" }}>
                  {s.ticker}
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

import type { ScreenStock, Confidence } from "../../lib/types";
import { confidenceColors, confidenceIcons } from "../../lib/colors";

interface Props {
  stocks: ScreenStock[];
  universe: string;
  date: string;
  screened: number;
}

export function SignalBanner({ stocks, universe, date, screened }: Props) {
  const cbPicks = stocks.filter((s) => s.classification === "CONVICTION BUY");
  const count = cbPicks.length;
  const isZero = count === 0;

  // Confidence distribution
  const confCounts: Record<Confidence, number> = { HIGH: 0, MODERATE: 0, LOW: 0 };
  for (const s of cbPicks) {
    if (s.confidence) confCounts[s.confidence]++;
  }

  // Classification distribution for the bar
  const bucketOrder = [
    "CONVICTION BUY", "QUALITY GROWTH PREMIUM", "WATCH LIST", "HOLD",
    "OVERVALUED QUALITY", "OVERVALUED", "VALUE TRAP", "AVOID",
  ] as const;

  const bucketCounts = new Map<string, number>();
  for (const s of stocks) {
    bucketCounts.set(s.classification, (bucketCounts.get(s.classification) || 0) + 1);
  }

  return (
    <div className="flex flex-col items-center pt-16 pb-10 px-8">
      {/* Logotype */}
      <span className="font-mono text-sm font-medium tracking-[0.12em] uppercase mb-1"
            style={{ color: "var(--color-text-muted)" }}>
        ASSAY
      </span>
      <span className="text-sm mb-12" style={{ color: "var(--color-text-secondary)" }}>
        {universe} · Value + Quality
      </span>

      {/* Hero number */}
      <span
        className="font-mono text-[80px] leading-none font-semibold mb-1"
        style={{ color: isZero ? "#eab308" : "var(--color-text-primary)" }}
      >
        {count}
      </span>
      <span className="text-lg mb-0.5" style={{ color: "var(--color-text-secondary)" }}>
        {isZero ? "nothing qualifies today" : "conviction buys"}
      </span>
      <span className="text-[13px] mb-8" style={{ color: "var(--color-text-muted)" }}>
        from {screened} screened
      </span>

      {/* Confidence dots (only if picks exist) */}
      {count > 0 && (
        <div className="flex gap-6 mb-10">
          {(["HIGH", "MODERATE", "LOW"] as Confidence[]).map((tier) => (
            <div key={tier} className="flex items-center gap-1.5">
              <span className="text-xs" style={{ color: confidenceColors[tier] }}>
                {confidenceIcons[tier]}
              </span>
              <span className="font-mono text-[13px]" style={{ color: "var(--color-text-secondary)" }}>
                {tier} {confCounts[tier]}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Zero-pick context */}
      {isZero && (
        <p className="text-[13px] max-w-md text-center mb-10" style={{ color: "var(--color-text-secondary)" }}>
          Nothing in the {universe} passes all filters simultaneously.
          This has happened in 5 of 16 historical quarters.
          The system couldn't find a single stock where cheapness, quality, and
          financial health all aligned.
        </p>
      )}

      {/* Date */}
      <span className="text-[13px] mb-8" style={{ color: "var(--color-text-muted)" }}>
        {date}
      </span>

      {/* Classification bar */}
      <div className="w-full max-w-2xl">
        <div className="flex h-1 rounded-full overflow-hidden">
          {bucketOrder.map((bucket) => {
            const n = bucketCounts.get(bucket) || 0;
            if (n === 0) return null;
            const pct = (n / stocks.length) * 100;
            const colors: Record<string, string> = {
              "CONVICTION BUY": "var(--color-cb)",
              "QUALITY GROWTH PREMIUM": "var(--color-qgp)",
              "WATCH LIST": "var(--color-wl)",
              HOLD: "var(--color-hold)",
              "OVERVALUED QUALITY": "var(--color-oq)",
              OVERVALUED: "var(--color-ov)",
              "VALUE TRAP": "var(--color-vt)",
              AVOID: "var(--color-avoid)",
            };
            return (
              <div
                key={bucket}
                style={{ width: `${pct}%`, backgroundColor: colors[bucket], opacity: 0.6 }}
                title={`${bucket}: ${n}`}
              />
            );
          })}
        </div>
        <div className="flex justify-between mt-1.5 text-[10px] tracking-wide"
             style={{ color: "var(--color-text-muted)" }}>
          <span>CB {bucketCounts.get("CONVICTION BUY") || 0}</span>
          <span>WL {bucketCounts.get("WATCH LIST") || 0}</span>
          <span>HOLD {bucketCounts.get("HOLD") || 0}</span>
          <span>AVOID {bucketCounts.get("AVOID") || 0}</span>
        </div>
      </div>
    </div>
  );
}

import type { ScreenStock, Confidence } from "../../lib/types";
import { confidenceColors, confidenceIcons } from "../../lib/colors";
import { useCountUp } from "../../hooks/useCountUp";

interface Props {
  stocks: ScreenStock[];
  universe: string;
  date: string;
  screened: number;
}

export function SignalBanner({ stocks, universe, date, screened }: Props) {
  const cbPicks = stocks.filter((s) => s.classification === "RESEARCH CANDIDATE");
  const count = cbPicks.length;
  const isZero = count === 0;
  // Hero count-up — 900ms ease-out-expo. Zero stays still (restraint).
  const animatedCount = useCountUp(count, 900);
  const displayCount = isZero ? 0 : Math.round(animatedCount);

  // Confidence distribution
  const confCounts: Record<Confidence, number> = { HIGH: 0, MODERATE: 0, LOW: 0 };
  for (const s of cbPicks) {
    if (s.confidence) confCounts[s.confidence]++;
  }

  // Classification distribution for the bar
  const bucketOrder = [
    "RESEARCH CANDIDATE", "QUALITY GROWTH PREMIUM", "WATCH LIST", "HOLD",
    "OVERVALUED QUALITY", "OVERVALUED", "VALUE TRAP", "AVOID",
  ] as const;

  const bucketCounts = new Map<string, number>();
  for (const s of stocks) {
    bucketCounts.set(s.classification, (bucketCounts.get(s.classification) || 0) + 1);
  }

  return (
    <div className="flex flex-col items-center pt-10 sm:pt-16 pb-8 sm:pb-10 px-4 sm:px-8">
      {/* Logotype */}
      <span className="font-mono text-sm font-medium tracking-[0.12em] uppercase mb-1 anim-fade"
            style={{ color: "var(--color-text-muted)" }}>
        ASSAY
      </span>
      <span className="text-sm mb-12 anim-fade" style={{ color: "var(--color-text-secondary)", animationDelay: "60ms" }}>
        {universe} · Value + Quality
      </span>

      {/* Hero number — count-up tells the story of "earned" */}
      <span
        className="font-mono text-[56px] sm:text-[80px] leading-none font-semibold mb-1 tabular-nums"
        style={{ color: isZero ? "#eab308" : "var(--color-text-primary)" }}
      >
        {displayCount}
      </span>
      <span className="text-lg mb-0.5 anim-fade-up" style={{ color: "var(--color-text-secondary)", animationDelay: "300ms" }}>
        {isZero ? "nothing qualifies today" : "conviction buys"}
      </span>
      <span className="text-[13px] mb-8 anim-fade" style={{ color: "var(--color-text-muted)", animationDelay: "500ms" }}>
        from {screened} screened
      </span>

      {/* Confidence dots (only if picks exist) */}
      {count > 0 && (
        <div className="flex gap-6 mb-10">
          {(["HIGH", "MODERATE", "LOW"] as Confidence[]).map((tier, i) => (
            <div key={tier} className="flex items-center gap-1.5 anim-fade-up"
                 style={{ animationDelay: `${700 + i * 80}ms` }}>
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
        <p className="text-[13px] max-w-md text-center mb-10 anim-fade-up"
           style={{ color: "var(--color-text-secondary)", animationDelay: "400ms" }}>
          Nothing in the {universe} passes all filters simultaneously.
          This has happened in 5 of 16 historical quarters.
          The system couldn't find a single stock where cheapness, quality, and
          financial health all aligned.
        </p>
      )}

      {/* Date */}
      <span className="text-[13px] mb-8 anim-fade"
            style={{ color: "var(--color-text-muted)", animationDelay: "800ms" }}>
        {date}
      </span>

      {/* Classification bar — assembles itself, stratigraphy of the universe */}
      <div className="w-full max-w-2xl anim-fade" style={{ animationDelay: "850ms" }}>
        <div className="flex h-1 rounded-full overflow-hidden">
          {bucketOrder.map((bucket, bi) => {
            const n = bucketCounts.get(bucket) || 0;
            if (n === 0) return null;
            const pct = (n / stocks.length) * 100;
            const colors: Record<string, string> = {
              "RESEARCH CANDIDATE": "var(--color-cb)",
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
                className="h-full"
                style={{
                  width: `${pct}%`,
                  backgroundColor: colors[bucket],
                  opacity: 0.6,
                  transform: "scaleX(0)",
                  transformOrigin: "left center",
                  animation: `a-draw-x 320ms var(--ease-out-quart) ${950 + bi * 40}ms forwards`,
                }}
                title={`${bucket}: ${n}`}
              />
            );
          })}
        </div>
        <div className="flex justify-between mt-1.5 text-[10px] tracking-wide anim-fade"
             style={{ color: "var(--color-text-muted)", animationDelay: "1300ms" }}>
          <span>CB {bucketCounts.get("RESEARCH CANDIDATE") || 0}</span>
          <span>WL {bucketCounts.get("WATCH LIST") || 0}</span>
          <span>HOLD {bucketCounts.get("HOLD") || 0}</span>
          <span>AVOID {bucketCounts.get("AVOID") || 0}</span>
        </div>
      </div>
    </div>
  );
}

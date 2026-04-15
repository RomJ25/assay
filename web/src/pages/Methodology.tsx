export function Methodology() {
  return (
    <div className="px-8 py-10 max-w-3xl">
      <h1 className="text-xl font-semibold mb-1">How It Works</h1>
      <p className="text-[13px] mb-8" style={{ color: "var(--color-text-secondary)" }}>
        The complete methodology behind Assay's scoring and classification system.
      </p>

      <Section title="Value Score (0-100)">
        <p>Percentile rank by <strong>Earnings Yield</strong> (EBIT / Enterprise Value). Cheapest stock = 100.</p>
        <p>Composite of 70% earnings yield rank + 30% free cash flow yield rank. Negative EBIT/FCF rank at the bottom, not excluded.</p>
        <p className="text-[12px] mt-2" style={{ color: "var(--color-text-muted)" }}>
          Based on Carlisle's Acquirer's Multiple (EV/EBIT): 17.9% CAGR over 44 years.
        </p>
      </Section>

      <Section title="Quality Score (0-100)">
        <p>40% <strong>Piotroski F-Score</strong> (9 binary financial health criteria, normalized 0-100) + 40% <strong>Profitability</strong> ((GP + R&D) / Assets) percentile rank + 20% <strong>Safety</strong> (inverse beta + inverse leverage).</p>
        <p className="text-[12px] mt-2" style={{ color: "var(--color-text-muted)" }}>
          Piotroski (2000): 13.4% annual outperformance. Novy-Marx & Medhat (2025): (GP+R&D)/Assets dominates plain GP/Assets. Asness et al. (2019): safety has 55-66 bps/month alpha.
        </p>
      </Section>

      <Section title="Piotroski F-Score (9 Criteria)">
        <div className="space-y-1 mt-2">
          {[
            { group: "Profitability", items: ["Net Income > 0", "Operating Cash Flow > 0", "ROA improving year-over-year"] },
            { group: "Balance Sheet", items: ["Cash earnings > Accrual earnings (OCF > NI)", "Debt ratio decreasing", "Current ratio increasing"] },
            { group: "Efficiency", items: ["No share dilution", "Gross margin improving", "Asset turnover improving"] },
          ].map((g) => (
            <div key={g.group} className="mb-3">
              <div className="text-[11px] uppercase tracking-[0.06em] mb-1 font-medium" style={{ color: "var(--color-text-muted)" }}>{g.group}</div>
              {g.items.map((item, i) => (
                <div key={i} className="text-[13px] pl-4 py-0.5" style={{ color: "var(--color-text-secondary)" }}>
                  {i + 1 + (g.group === "Balance Sheet" ? 3 : g.group === "Efficiency" ? 6 : 0)}. {item}
                </div>
              ))}
            </div>
          ))}
        </div>
        <p className="text-[12px] mt-1" style={{ color: "var(--color-text-muted)" }}>
          Each criterion is binary (0 or 1). Raw F-Score = sum of 9 criteria (0-9). Minimum 6/9 required for CONVICTION BUY.
        </p>
      </Section>

      <Section title="Conviction Score">
        <p><strong>Geometric mean</strong> of Value and Quality: √(V × Q).</p>
        <p>Both dimensions must be high. A stock that's very cheap but low quality (value trap) gets punished. A stock that's high quality but expensive (overvalued quality) also gets punished.</p>
      </Section>

      <Section title="Classification Matrix">
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b" style={{ borderColor: "var(--color-border)" }}>
                <th className="text-left py-2 px-2" style={{ color: "var(--color-text-muted)" }}></th>
                <th className="text-center py-2 px-2" style={{ color: "var(--color-text-muted)" }}>Q ≥ 70</th>
                <th className="text-center py-2 px-2" style={{ color: "var(--color-text-muted)" }}>Q 40-70</th>
                <th className="text-center py-2 px-2" style={{ color: "var(--color-text-muted)" }}>Q &lt; 40</th>
              </tr>
            </thead>
            <tbody>
              {[
                { label: "V ≥ 70", cells: ["CONVICTION BUY", "WATCH LIST", "VALUE TRAP"] },
                { label: "V 40-70", cells: ["QUALITY GROWTH", "HOLD", "AVOID"] },
                { label: "V < 40", cells: ["OVERVALUED QUALITY", "OVERVALUED", "AVOID"] },
              ].map((row) => (
                <tr key={row.label} className="border-b" style={{ borderColor: "var(--color-border)" }}>
                  <td className="py-2 px-2 font-mono text-[11px]" style={{ color: "var(--color-text-muted)" }}>{row.label}</td>
                  {row.cells.map((cell) => (
                    <td key={cell} className="py-2 px-2 text-center text-[11px]">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Safety Gates">
        <p><strong>F-Score Gate:</strong> CONVICTION BUY requires F-Score ≥ 6/9. Below 6 → downgraded to WATCH LIST.</p>
        <p><strong>Momentum Gate:</strong> Bottom 25% by 12-1 month momentum → downgraded to WATCH LIST. Catches falling knives.</p>
        <p><strong>Revenue Gate:</strong> 2+ consecutive years of declining revenue → downgraded to WATCH LIST.</p>
        <p className="text-[12px] mt-2" style={{ color: "var(--color-text-muted)" }}>
          Momentum gate validated: 98 victims averaged +2.6% vs CB's +4.5% (12-quarter investigation).
        </p>
      </Section>

      <Section title="Confidence Levels">
        <p>Within CONVICTION BUY, confidence = min(V - 70, Q - 70):</p>
        <ul className="text-[13px] pl-4 space-y-1 mt-2" style={{ color: "var(--color-text-secondary)" }}>
          <li><strong style={{ color: "#22c55e" }}>HIGH:</strong> Both V, Q ≥ 85 (margin ≥ 15)</li>
          <li><strong style={{ color: "#eab308" }}>MODERATE:</strong> Both V, Q ≥ 75 (margin ≥ 5)</li>
          <li><strong style={{ color: "#ef4444" }}>LOW:</strong> At least one score barely above 70</li>
        </ul>
        <p className="text-[12px] mt-2" style={{ color: "var(--color-text-muted)" }}>
          Aggregate returns: HIGH +6.7% &gt; MOD +5.4% &gt; LOW +3.3%. Meaningful in expectation, not per-quarter.
        </p>
      </Section>

      <Section title="What This Is Not">
        <p>This is not a prediction engine. It does not forecast prices or use machine learning.</p>
        <p>Individual CB picks beat the universe mean 52% of the time with a 1.05× win/loss ratio. The screener's value comes from systematic sector tilting toward cheap, quality sectors — not individual stock selection.</p>
        <p className="font-medium mt-2">It is a disciplined filter, not an alpha engine.</p>
      </Section>

      <Section title="Academic Foundation">
        <ul className="text-[13px] space-y-2 mt-2" style={{ color: "var(--color-text-secondary)" }}>
          <li><strong>Carlisle</strong> — Acquirer's Multiple (EV/EBIT): 17.9% CAGR over 44 years</li>
          <li><strong>Piotroski (2000)</strong> — F-Score: 13.4% long-only excess return, 23% long-short differential</li>
          <li><strong>Novy-Marx (2013)</strong> — Gross Profitability: predictive power equal to book-to-market</li>
          <li><strong>Novy-Marx & Medhat (2025)</strong> — (GP + R&D) / Assets dominates plain GP/Assets over 50 years</li>
          <li><strong>Asness, Frazzini & Pedersen (2019)</strong> — QMJ Safety: low beta + low leverage = crisis convexity</li>
          <li><strong>Jegadeesh & Titman (1993)</strong> — 12-1 month momentum: persistent return premium</li>
          <li><strong>Fama & French (2012)</strong> — Factor premiums are 2-3x stronger in mid-cap than large-cap</li>
          <li><strong>Schwartz & Hanauer (2024)</strong> — Formula Investing: unified comparison of Piotroski, Magic Formula, Acquirer's Multiple</li>
        </ul>
      </Section>

      <div className="mt-12 text-center text-[12px] italic" style={{ color: "var(--color-text-muted)" }}>
        Research tool for idea generation. Not financial advice.<br />
        Past academic performance does not guarantee future results.
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <h2 className="text-base font-semibold mb-3">{title}</h2>
      <div className="text-[13px] space-y-2" style={{ color: "var(--color-text-secondary)" }}>
        {children}
      </div>
    </div>
  );
}

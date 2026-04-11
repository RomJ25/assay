import { useState } from "react";
import { useScreenData } from "../hooks/useScreenData";
import { SignalBanner } from "../components/dashboard/SignalBanner";
import { ConvictionTable } from "../components/picks/ConvictionTable";
import { StockSheet } from "../components/stock/StockSheet";

export function Home() {
  const { data, loading, error } = useScreenData();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-48 h-1 rounded-full overflow-hidden" style={{ backgroundColor: "var(--color-surface-2)" }}>
          <div className="h-full rounded-full animate-pulse" style={{ backgroundColor: "var(--color-cb)", width: "40%" }} />
        </div>
        <p className="mt-4 text-[13px]" style={{ color: "var(--color-text-muted)" }}>Loading screen data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] px-8">
        <p className="text-lg mb-2" style={{ color: "#ef4444" }}>Unable to load screen data</p>
        <p className="text-[13px] mb-4" style={{ color: "var(--color-text-secondary)" }}>{error}</p>
        <p className="text-[13px]" style={{ color: "var(--color-text-muted)" }}>
          Run the screener first: <code className="font-mono">python main.py</code>
        </p>
      </div>
    );
  }

  if (!data) return null;

  const selectedStock = selectedTicker ? data.stocks.find((s) => s.ticker === selectedTicker) : null;

  return (
    <div>
      <SignalBanner
        stocks={data.stocks}
        universe={data.universe}
        date={data.date}
        screened={data.screened}
      />

      <ConvictionTable stocks={data.stocks} onSelectStock={setSelectedTicker} />

      {/* Caveat footer */}
      <div className="text-center py-8 text-[12px] italic" style={{ color: "var(--color-text-muted)" }}>
        Research tool for idea generation. Not a trading signal. Minimum 3-5 year horizon.
      </div>

      {/* Stock Deep Dive */}
      {selectedStock && (
        <StockSheet stock={selectedStock} onClose={() => setSelectedTicker(null)} />
      )}
    </div>
  );
}

import { useState, useCallback } from "react";

interface Props {
  onComplete: () => void;
}

export function RunScreener({ onComplete }: Props) {
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState("");
  const [progress, setProgress] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    include_financials: false,
    sector_relative: false,
    refresh: false,
  });

  const runScreener = useCallback(async () => {
    setRunning(true);
    setPhase("Starting...");
    setProgress(0);
    setShowSettings(false);

    try {
      const response = await fetch("/api/v1/screen/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        const err = await response.json();
        setPhase(`Error: ${err.detail || "Unknown error"}`);
        setRunning(false);
        return;
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value);
          const lines = text.split("\n").filter((l) => l.startsWith("data: "));
          for (const line of lines) {
            try {
              const data = JSON.parse(line.slice(6));
              setPhase(data.phase || "");
              setProgress(data.progress || 0);
              if (data.done) {
                setRunning(false);
                if (data.progress === 100) {
                  onComplete();
                }
              }
            } catch {}
          }
        }
      }
    } catch (e: any) {
      setPhase(`Connection error: ${e.message}`);
    }
    setRunning(false);
  }, [settings, onComplete]);

  return (
    <div className="relative">
      {/* Progress bar (thin, top of viewport) */}
      {running && (
        <div className="fixed top-0 left-0 right-0 z-[70] h-0.5" style={{ backgroundColor: "var(--color-surface-2)" }}>
          <div className="h-full transition-all duration-500 ease-out"
               style={{ width: `${Math.max(progress, 5)}%`, backgroundColor: "var(--color-cb)" }} />
        </div>
      )}

      {/* Button */}
      <button
        className="flex items-center gap-2 rounded-md px-3 py-1.5 text-[12px] font-medium transition-all duration-150"
        style={{
          backgroundColor: running ? "var(--color-surface-2)" : "transparent",
          border: "1px solid var(--color-border)",
          color: running ? "var(--color-text-muted)" : "var(--color-text-secondary)",
          cursor: running ? "not-allowed" : "pointer",
        }}
        onClick={() => running ? null : setShowSettings(!showSettings)}
        disabled={running}
      >
        {running ? (
          <>
            <span className="animate-spin text-[10px]">⟳</span>
            {phase}
          </>
        ) : (
          <>▶ Run</>
        )}
      </button>

      {/* Settings dropdown */}
      {showSettings && !running && (
        <div className="absolute right-0 top-full mt-2 w-64 rounded-lg p-4 shadow-xl z-50"
             style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}>
          <div className="text-[11px] uppercase tracking-[0.06em] mb-3 font-medium"
               style={{ color: "var(--color-text-muted)" }}>
            Screener Settings
          </div>

          <label className="flex items-center gap-2 py-1.5 cursor-pointer">
            <input type="checkbox" checked={settings.include_financials}
                   onChange={(e) => setSettings({ ...settings, include_financials: e.target.checked })}
                   className="rounded" />
            <span className="text-[13px]">Include Financials/RE</span>
          </label>

          <label className="flex items-center gap-2 py-1.5 cursor-pointer">
            <input type="checkbox" checked={settings.sector_relative}
                   onChange={(e) => setSettings({ ...settings, sector_relative: e.target.checked })}
                   className="rounded" />
            <span className="text-[13px]">Sector-Relative Scoring</span>
          </label>

          <label className="flex items-center gap-2 py-1.5 cursor-pointer">
            <input type="checkbox" checked={settings.refresh}
                   onChange={(e) => setSettings({ ...settings, refresh: e.target.checked })}
                   className="rounded" />
            <span className="text-[13px]">Refresh Data (bypass cache)</span>
          </label>

          <button
            className="w-full mt-3 rounded-md py-2 text-[13px] font-medium transition-colors"
            style={{ backgroundColor: "var(--color-cb)", color: "#000" }}
            onClick={runScreener}
          >
            Run Screener
          </button>

          <p className="text-[10px] mt-2 text-center" style={{ color: "var(--color-text-muted)" }}>
            Takes ~60 seconds
          </p>
        </div>
      )}
    </div>
  );
}

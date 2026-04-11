import { useState, useEffect, useRef, useCallback } from "react";
import { classificationColors } from "../../lib/colors";
import type { SearchResult } from "../../lib/types";

interface Props {
  onSelect: (ticker: string) => void;
}

export function SearchPalette({ onSelect }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Cmd+K to open
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
      setResults([]);
      setSelected(0);
    }
  }, [open]);

  // Search on query change
  useEffect(() => {
    if (!query || query.length < 1) { setResults([]); return; }
    const controller = new AbortController();
    fetch(`/api/v1/search?q=${encodeURIComponent(query)}`, { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => { setResults(d.results || []); setSelected(0); })
      .catch(() => {});
    return () => controller.abort();
  }, [query]);

  const handleSelect = useCallback((ticker: string) => {
    setOpen(false);
    onSelect(ticker);
  }, [onSelect]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSelected((s) => Math.min(s + 1, results.length - 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); setSelected((s) => Math.max(s - 1, 0)); }
    if (e.key === "Enter" && results[selected]) { handleSelect(results[selected].ticker); }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center pt-[15vh]" onClick={() => setOpen(false)}>
      <div className="absolute inset-0 transition-opacity duration-200"
           style={{ backgroundColor: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }} />

      <div className="relative w-full max-w-lg rounded-xl overflow-hidden shadow-2xl"
           style={{ backgroundColor: "var(--color-surface-1)", border: "1px solid var(--color-border)" }}
           onClick={(e) => e.stopPropagation()}>

        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b" style={{ borderColor: "var(--color-border)" }}>
          <span className="text-[14px]" style={{ color: "var(--color-text-muted)" }}>⌘</span>
          <input
            ref={inputRef}
            type="text"
            placeholder="Search by ticker or company..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent outline-none text-[14px]"
            style={{ color: "var(--color-text-primary)" }}
          />
          <kbd className="text-[10px] rounded px-1.5 py-0.5 font-mono"
               style={{ backgroundColor: "var(--color-surface-2)", color: "var(--color-text-muted)" }}>
            ESC
          </kbd>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="max-h-[320px] overflow-y-auto py-1">
            {results.map((r, i) => {
              const clColor = (classificationColors as any)[r.classification] || "#71717a";
              return (
                <button
                  key={r.ticker}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors duration-75"
                  style={{ backgroundColor: i === selected ? "var(--color-surface-2)" : "transparent" }}
                  onClick={() => handleSelect(r.ticker)}
                  onMouseEnter={() => setSelected(i)}
                >
                  <span className="font-mono text-[13px] font-semibold w-12">{r.ticker}</span>
                  <span className="text-[13px] flex-1 truncate" style={{ color: "var(--color-text-secondary)" }}>
                    {r.company}
                  </span>
                  <span className="text-[10px] rounded-full px-2 py-0.5 font-medium shrink-0"
                        style={{ backgroundColor: `${clColor}20`, color: clColor }}>
                    {r.classification}
                  </span>
                  <span className="font-mono text-[11px] w-16 text-right" style={{ color: "var(--color-text-muted)" }}>
                    {r.conviction_score?.toFixed(1)}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Empty state */}
        {query && results.length === 0 && (
          <div className="py-8 text-center text-[13px]" style={{ color: "var(--color-text-muted)" }}>
            No stocks match "{query}"
          </div>
        )}

        {/* Hint */}
        {!query && (
          <div className="py-6 text-center text-[12px]" style={{ color: "var(--color-text-muted)" }}>
            Type a ticker or company name to search {" "}
            <span className="font-mono">↑↓</span> to navigate {" "}
            <span className="font-mono">↵</span> to select
          </div>
        )}
      </div>
    </div>
  );
}

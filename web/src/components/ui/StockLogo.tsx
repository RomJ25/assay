import { useState } from "react";

interface Props {
  ticker: string;
  company: string;
  size?: number;
}

export function StockLogo({ ticker, company, size = 24 }: Props) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    // Letter avatar fallback
    return (
      <div
        className="flex items-center justify-center rounded-md font-mono font-medium shrink-0"
        style={{
          width: size,
          height: size,
          backgroundColor: "var(--color-surface-2)",
          color: "var(--color-text-muted)",
          fontSize: size * 0.45,
        }}
      >
        {company.charAt(0).toUpperCase()}
      </div>
    );
  }

  return (
    <img
      src={`/api/v1/logo/${ticker}`}
      alt={ticker}
      className="rounded-md shrink-0 object-contain"
      style={{
        width: size,
        height: size,
        backgroundColor: "rgba(255,255,255,0.92)",
        border: "1px solid var(--color-border)",
      }}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}

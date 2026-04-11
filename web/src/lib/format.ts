/* Number and currency formatting utilities. */

export function fmtScore(val: number | null): string {
  if (val == null) return "—";
  return val.toFixed(1);
}

export function fmtPercent(val: number | null, decimals = 1): string {
  if (val == null) return "—";
  return `${val >= 0 ? "+" : ""}${val.toFixed(decimals)}%`;
}

export function fmtPrice(val: number | null): string {
  if (val == null) return "—";
  if (val >= 100) return `$${Math.round(val)}`;
  return `$${val.toFixed(2)}`;
}

export function fmtMarketCap(val: number | null): string {
  if (val == null) return "—";
  if (val >= 1e12) return `$${(val / 1e12).toFixed(1)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(0)}M`;
  return `$${val.toFixed(0)}`;
}

export function fmtFScore(val: number | null): string {
  if (val == null) return "—";
  return `${val}/9`;
}

export function fmtAnalyst(target: number | null, upside: number | null): string {
  if (target == null) return "—";
  const price = fmtPrice(target);
  if (upside != null) {
    return `${price} (${upside >= 0 ? "+" : ""}${upside.toFixed(0)}%)`;
  }
  return price;
}

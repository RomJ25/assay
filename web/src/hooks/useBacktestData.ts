import { useState, useEffect } from "react";

export interface BacktestQuarter {
  date: string;
  next_date: string;
  num_picks: number;
  portfolio_return: number;
  universe_return: number;
  spy_return: number;
  excess_return: number;
  turnover: number | null;
}

export interface BacktestPick {
  quarter: string;
  ticker: string;
  sector: string;
  value_score: number;
  quality_score: number;
  piotroski_f: number;
  momentum_pct: number;
}

export interface BacktestResponse {
  date: string;
  quarters: BacktestQuarter[];
  picks: BacktestPick[];
}

export function useBacktestData() {
  const [data, setData] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/v1/backtest")
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}: ${r.statusText}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}

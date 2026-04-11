/* TypeScript types matching Python dataclasses exactly. */

export type Classification =
  | "CONVICTION BUY"
  | "QUALITY GROWTH PREMIUM"
  | "WATCH LIST"
  | "HOLD"
  | "OVERVALUED QUALITY"
  | "OVERVALUED"
  | "VALUE TRAP"
  | "AVOID";

export type Confidence = "HIGH" | "MODERATE" | "LOW";

export interface PiotroskiCriterion {
  pass: boolean;
  value?: number;
  current?: number;
  prior?: number;
  ocf?: number;
  ni?: number;
}

export interface PiotroskiBreakdown {
  raw_score: number;
  criteria: Record<string, PiotroskiCriterion>;
}

export interface ScreenStock {
  ticker: string;
  company: string;
  sector: string;
  price: number;
  value_score: number;
  quality_score: number;
  conviction_score: number;
  classification: Classification;
  confidence: Confidence | null;
  trajectory_score: number | null;
  piotroski_f: number;
  earnings_yield: number | null;
  fcf_yield: number | null;
  momentum_12m: number | null;
  gross_profitability: number | null;
  growth_score: number | null;
  piotroski_breakdown: PiotroskiBreakdown;
  // Valuation context
  dcf_bear: number | null;
  dcf_base: number | null;
  dcf_bull: number | null;
  analyst_target: number | null;
  analyst_upside: number | null;
  pct_from_52w_high: number | null;
  // Additional metrics
  revenue_cagr_3yr: number | null;
  gross_margin: number | null;
  pe_ratio: number | null;
  ev_ebitda: number | null;
  dividend_yield: number | null;
  beta: number | null;
  market_cap: number | null;
}

export interface ScreenResponse {
  universe: string;
  date: string;
  screened: number;
  stocks: ScreenStock[];
}

export interface SearchResult {
  ticker: string;
  company: string;
  classification: Classification;
  value_score: number;
  quality_score: number;
  conviction_score: number;
  confidence: Confidence | null;
}

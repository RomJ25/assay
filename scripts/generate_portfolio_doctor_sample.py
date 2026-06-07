"""Generate the Portfolio Doctor sample artifact.

Reads a sample portfolio CSV (ticker, position_type, thesis, review_date),
loads the latest two full screens from results/, and emits one Markdown +
one HTML report per portfolio under examples/.

Reuses production helpers:
  api.routes._load_stocks            (legacy-label-aware loader)
  api.routes._explain_change         (per-ticker diff explainer)

The artifact is a *demo* of the format. Real value compounds on quarterly
cadence. Bear-case bullets are templated scaffolding — expect a hand-edit
pass before sending to test users.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

# Make the project importable when invoked as `python scripts/...`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.routes import _explain_change, _load_stocks  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
EXAMPLES_DIR = REPO_ROOT / "examples"

REPORT_DATE = date.today().isoformat()


# ── Loaders ────────────────────────────────────────────────────────────


def find_full_screens() -> list[Path]:
    """Return screen JSONs sorted newest → oldest, filtered to full snapshots."""
    files = sorted(RESULTS_DIR.glob("screen_*.json"), reverse=True)
    return [p for p in files if p.stat().st_size > 100_000]


def load_portfolio(csv_path: Path) -> list[dict]:
    """Load the sample portfolio CSV. Tolerates missing optional columns."""
    rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["ticker"] = row["ticker"].strip().upper()
            row["position_type"] = (row.get("position_type") or "holding").strip().lower()
            row["thesis"] = (row.get("thesis") or "").strip()
            row["review_date"] = (row.get("review_date") or "").strip()
            rows.append(row)
    return rows


# ── Per-ticker analysis ────────────────────────────────────────────────


@dataclass
class TickerReport:
    """One row of the report — everything we need to render Markdown + HTML."""

    ticker: str
    position_type: str  # holding / watchlist
    thesis: str
    review_date: str
    snapshot: dict  # the full per-ticker dict from current screen, or {}
    diff: dict | None  # _explain_change(prior, current) or None
    review_state: str  # SELL_REVIEW / MONITOR / NO_ACTION / DATA_INSUFFICIENT / NOT_IN_UNIVERSE
    severity: str  # high / medium / low
    primary_reason: str
    next_action: str
    bear_case: list[str] = field(default_factory=list)
    research_checklist: list[str] = field(default_factory=list)


def _gates_fired(stock: dict) -> list[str]:
    return [g for g in ("f_gate_fired", "momentum_gate_fired", "revenue_gate_fired") if stock.get(g)]


def _data_quality(stock: dict) -> tuple[str, list[str]]:
    """Return (grade, warnings). Tolerates missing data_quality field on legacy snapshots."""
    dq = stock.get("data_quality")
    if not isinstance(dq, dict):
        return ("unknown", [])
    grade = dq.get("grade", "unknown")
    warnings = list(dq.get("warnings") or [])
    return (grade, warnings)


def compute_review_state(stock: dict, diff: dict | None, review_date: str) -> tuple[str, str, str]:
    """Return (review_state, severity, primary_reason)."""
    if not stock:
        return ("NOT_IN_UNIVERSE", "low", "Ticker not in current S&P 500 snapshot")

    grade, _ = _data_quality(stock)
    if grade == "red":
        return ("DATA_INSUFFICIENT", "high", "Required fundamentals missing — score not reliable")

    gates_now = _gates_fired(stock)
    classification = stock.get("classification") or "UNKNOWN"
    raw = stock.get("raw_classification") or classification

    severe_gate_fired = stock.get("revenue_gate_fired") or stock.get("f_gate_fired")
    newly_fired = (diff or {}).get("newly_fired", [])
    f_now = stock.get("piotroski_f")
    f_before = ((diff or {}).get("metric_deltas") or {}).get("piotroski_f", {}).get("previous")
    f_dropped_2plus = (
        f_now is not None and f_before is not None and isinstance(f_before, (int, float)) and (f_before - f_now) >= 2
    )

    review_overdue = False
    if review_date:
        try:
            review_overdue = datetime.fromisoformat(review_date).date() < date.today()
        except ValueError:
            pass

    # F < 5 absolute is a sell-review signal regardless of which gate fired in the screening
    # pipeline. Gates only fire on RESEARCH CANDIDATE candidates; a low F on an OVERVALUED or
    # HOLD ticker passes through silently and that's exactly the kind of evidence Portfolio
    # Doctor exists to surface.
    f_low_absolute = isinstance(f_now, int) and f_now < 5

    if severe_gate_fired or (newly_fired and raw == "RESEARCH CANDIDATE") or f_dropped_2plus or f_low_absolute:
        reasons = []
        if stock.get("revenue_gate_fired"):
            reasons.append("revenue declined for 2+ consecutive years")
        if stock.get("f_gate_fired"):
            reasons.append(f"F-score gate fired (F={f_now}/9 below minimum 6)")
        if f_dropped_2plus:
            reasons.append(f"F-score dropped from {f_before} → {f_now}")
        if f_low_absolute and not stock.get("f_gate_fired"):
            reasons.append(f"low absolute Piotroski F-score (F={f_now}/9)")
        if newly_fired and raw == "RESEARCH CANDIDATE":
            reasons.append(f"new gate fired this quarter ({', '.join(newly_fired)})")
        return ("SELL_REVIEW", "high" if len(reasons) > 1 else "medium", "; ".join(reasons) or "evidence weakened")

    if classification == "AVOID":
        # AVOID isn't a "fired gate" — it's both V and Q low. Still warrants a sell-review look.
        return ("SELL_REVIEW", "medium", "AVOID classification (low value AND low quality scores)")

    # Substantive monitor reasons — yellow DQ is a *modifier*, not a sole trigger.
    substantive_reasons = []
    if stock.get("momentum_gate_fired"):
        substantive_reasons.append("momentum gate fired (bottom-quartile 12m momentum)")
    if classification == "OVERVALUED":
        substantive_reasons.append("OVERVALUED — V low while Q mid")
    if classification in ("WATCH LIST", "OVERVALUED QUALITY", "VALUE TRAP"):
        substantive_reasons.append(f"{classification} — mixed evidence, no all-clear")
    if review_overdue:
        substantive_reasons.append(f"thesis review date ({review_date}) is past")

    if substantive_reasons:
        # Yellow DQ amplifies severity but doesn't add an extra reason line that's noise.
        sev = "medium" if (len(substantive_reasons) > 1 or grade == "yellow") else "low"
        return ("MONITOR", sev, "; ".join(substantive_reasons))

    # Yellow DQ on an otherwise-clean ticker: surface in scorecard, don't promote to MONITOR.
    # The scorecard already shows the DQ chip + warnings — that's enough.
    return ("NO_ACTION", "low", "No flagged evidence change")


def next_research_action(stock: dict, review_state: str) -> str:
    if review_state == "NOT_IN_UNIVERSE":
        return "Confirm ticker is correct; this name is not in the S&P 500 snapshot used here."
    if review_state == "DATA_INSUFFICIENT":
        return "Re-pull fundamentals after next 10-Q; do not infer from current scores."

    grade, _ = _data_quality(stock)
    f_now = stock.get("piotroski_f")
    if review_state == "SELL_REVIEW":
        if stock.get("revenue_gate_fired"):
            return "Read the latest 10-K MD&A: is revenue decline cyclical or structural? Check segment trend."
        if stock.get("f_gate_fired") or (isinstance(f_now, int) and f_now < 5):
            return "Pull the Piotroski breakdown: which 3+ criteria are failing? Focus on profitability and accrual quality."
        return "Re-examine the original thesis. What changed materially since purchase?"
    if review_state == "MONITOR":
        if stock.get("momentum_gate_fired"):
            return "Check whether weak momentum reflects fundamentals not yet visible (revenue trend, margin pressure)."
        return "Re-check at next 10-Q. Update thesis if classification stays in this band 2+ quarters."
    return "No action required this quarter; revisit next filing cycle."


# ── Bear-case scaffolding ──────────────────────────────────────────────


def bear_case_bullets(stock: dict, diff: dict | None) -> list[str]:
    """Rule-based bullets. Hand-edit before final commit for ticker-specificity."""
    bullets = []
    if not stock:
        return ["Ticker not present in current snapshot — cannot synthesize a bear case from current data."]

    f = stock.get("piotroski_f")
    if isinstance(f, int) and f < 7:
        bullets.append(
            f"Accounting strength is mid-tier (F={f}/9). Several Piotroski criteria are failing, "
            "leaving room for further deterioration if any one of them tips."
        )

    if stock.get("revenue_gate_fired"):
        bullets.append(
            "Revenue has declined for 2+ consecutive years. The cheap valuation may be the market "
            "correctly pricing real business weakness, not a mispricing waiting to be corrected."
        )

    # Data-quality warnings live in §6 + the scorecard chip. Don't duplicate them here unless
    # the grade is red (then it's a hard sell-review-grade issue worth restating).
    grade, warnings = _data_quality(stock)
    if grade == "red":
        bullets.append(
            f"Required fundamentals missing ({'; '.join(warnings)}). Scores are not reliable; "
            "treat any conclusion drawn from them as provisional."
        )

    momentum = stock.get("momentum_12m")
    if isinstance(momentum, (int, float)) and momentum < 0:
        bullets.append(
            f"Trailing 12-month return is {momentum*100:.0f}% — the market may be discounting fundamentals "
            "that haven't yet shown up in annual financials."
        )
    elif stock.get("momentum_gate_fired"):
        bullets.append(
            "Momentum is bottom-quartile in the universe. Even when fundamentals look adequate, "
            "negative price action often precedes an evidence break by 1–2 quarters."
        )

    pe = stock.get("pe_ratio")
    fcf_y = stock.get("fcf_yield")
    if isinstance(pe, (int, float)) and pe > 30 and isinstance(fcf_y, (int, float)) and fcf_y < 3:
        bullets.append(
            f"Valuation requires continued execution (PE {pe:.0f}, FCF yield {fcf_y:.1f}%). "
            "Downside risk amplified if growth surprises to the downside."
        )

    if diff:
        cls_now = (diff.get("final_classification") or {}).get("current")
        cls_before = (diff.get("final_classification") or {}).get("previous")
        if cls_before == "RESEARCH CANDIDATE" and cls_now != "RESEARCH CANDIDATE":
            bullets.append(
                f"Lost RESEARCH CANDIDATE status this quarter ({cls_before} → {cls_now}). "
                "The original thesis needs re-examination, not just a refresh."
            )

    classification = stock.get("classification")
    if classification == "AVOID" and not bullets:
        bullets.append(
            "Both value AND quality scores are low (AVOID bucket). Cheap-and-bad rarely revalues — "
            "evidence has to improve before classification can."
        )

    if not bullets:
        bullets.append(
            "No prominent risk flags from the screen. That does not mean none exist — re-read the most "
            "recent 10-K risk factors before relying on this assessment."
        )

    return bullets


# ── Research checklist ─────────────────────────────────────────────────


def research_checklist(stock: dict, review_state: str) -> list[str]:
    if review_state in ("NO_ACTION", "NOT_IN_UNIVERSE"):
        return []
    items = [
        "Read the latest 10-Q MD&A (focus: revenue, margin, segment commentary)",
        "Check share-count trend (dilution offset to fundamental gains)",
        "Confirm whether free cash flow weakness is temporary or structural",
    ]
    if stock.get("revenue_gate_fired"):
        items.append("Compare 4-year revenue trajectory by segment")
    if stock.get("f_gate_fired"):
        items.append("Pull the Piotroski breakdown — which 3+ criteria are failing?")
    grade, _ = _data_quality(stock)
    if grade == "yellow":
        items.append("Verify primary-source filing date and refresh fundamentals if stale")
    items.append("Compare current evidence against the thesis as written at purchase")
    return items


# ── Build the full report data ─────────────────────────────────────────


def build_report_data(
    portfolio: list[dict],
    current_stocks: list[dict],
    prior_stocks: list[dict],
    current_date: str,
    prior_date: str,
    bear_case_overrides: dict[str, list[str]] | None = None,
) -> dict:
    current_by_ticker = {s["ticker"]: s for s in current_stocks}
    prior_by_ticker = {s["ticker"]: s for s in prior_stocks}
    overrides = bear_case_overrides or {}

    ticker_reports: list[TickerReport] = []
    for row in portfolio:
        t = row["ticker"]
        snap = current_by_ticker.get(t, {})
        prior = prior_by_ticker.get(t)
        diff = _explain_change(prior, snap) if prior and snap else None
        state, sev, primary = compute_review_state(snap, diff, row["review_date"])
        action = next_research_action(snap, state)
        bear = overrides.get(t) or bear_case_bullets(snap, diff)
        checklist = research_checklist(snap, state)
        ticker_reports.append(TickerReport(
            ticker=t, position_type=row["position_type"], thesis=row["thesis"],
            review_date=row["review_date"], snapshot=snap, diff=diff,
            review_state=state, severity=sev, primary_reason=primary,
            next_action=action, bear_case=bear, research_checklist=checklist,
        ))

    # Aggregate counts for the executive summary
    counts = {"SELL_REVIEW": 0, "MONITOR": 0, "NO_ACTION": 0, "DATA_INSUFFICIENT": 0, "NOT_IN_UNIVERSE": 0}
    dq_warnings = 0
    for r in ticker_reports:
        counts[r.review_state] = counts.get(r.review_state, 0) + 1
        grade, _ = _data_quality(r.snapshot)
        if grade in ("yellow", "red"):
            dq_warnings += 1

    return {
        "current_date": current_date,
        "prior_date": prior_date,
        "report_date": REPORT_DATE,
        "ticker_reports": ticker_reports,
        "counts": counts,
        "dq_warnings": dq_warnings,
        "total": len(ticker_reports),
    }


# ── Markdown rendering ─────────────────────────────────────────────────


SEVERITY_BADGE_MD = {"high": "🔴 high", "medium": "🟡 medium", "low": "⚪ low"}
DQ_BADGE_MD = {"green": "🟢 green", "yellow": "🟡 yellow", "red": "🔴 red", "unknown": "— unknown"}


def _fmt_pct(v) -> str:
    if not isinstance(v, (int, float)):
        return "—"
    return f"{v:.1f}%"


def _fmt_num(v, places: int = 1) -> str:
    if not isinstance(v, (int, float)):
        return "—"
    return f"{v:.{places}f}"


def render_markdown(rd: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Assay Portfolio Doctor — Sample Report")
    lines.append("")
    lines.append(f"_Generated {rd['report_date']} from S&P 500 snapshot dated {rd['current_date']} "
                 f"(prior baseline: {rd['prior_date']})_")
    lines.append("")
    lines.append("> **Public-data review tool. Not personalized financial advice.** Review flags, "
                 "not buy/sell recommendations. Minimum 3–5 year horizon. Selection alpha unproven; "
                 "this report organizes evidence — it does not forecast returns.")
    lines.append("")

    # 1. Executive summary
    lines.append("## 1. Executive summary")
    lines.append("")
    c = rd["counts"]
    lines.append(f"- **Reviewed:** {rd['total']} tickers")
    lines.append(f"- **Sell-review flags:** {c.get('SELL_REVIEW', 0)}")
    lines.append(f"- **Monitor flags:** {c.get('MONITOR', 0)}")
    lines.append(f"- **Data-quality warnings:** {rd['dq_warnings']}")
    lines.append(f"- **No-action holdings:** {c.get('NO_ACTION', 0)}")
    if c.get("DATA_INSUFFICIENT"):
        lines.append(f"- **Data insufficient:** {c['DATA_INSUFFICIENT']}")
    if c.get("NOT_IN_UNIVERSE"):
        lines.append(f"- **Not in universe:** {c['NOT_IN_UNIVERSE']}")
    lines.append("")
    lines.append("> _Important: these are research-review flags, not buy/sell recommendations._")
    lines.append("")

    # 2. What this report won't tell you
    lines.append("## 2. What this report won't tell you")
    lines.append("")
    lines.append("- **It will not predict returns.** Empirical testing on this system shows selection "
                 "alpha is unproven and too fragile to sell as a forecast — see the Bonferroni framework "
                 "in `docs/DESIGN_DECISIONS.md`.")
    lines.append("- **It will not tell you to buy or sell.** Every flag in this report is a *review* "
                 "trigger, not an action.")
    lines.append("- **It will not factor in your personal situation.** Tax basis, holding period, "
                 "concentration, time horizon, liquidity needs — all yours to weigh.")
    lines.append("- **It will not tell you the bull case.** The system is structurally biased toward "
                 "skepticism; the bull case is yours to build.")
    lines.append("- **It will not replace reading the 10-K.** The screen organizes public evidence; it "
                 "does not understand the business.")
    lines.append("")

    # 3. Holdings requiring review
    lines.append("## 3. Holdings requiring review")
    lines.append("")
    review_rows = [r for r in rd["ticker_reports"] if r.review_state not in ("NO_ACTION",)]
    if review_rows:
        lines.append("| Ticker | Review state | Severity | Primary reason | Data quality | Next research action |")
        lines.append("|---|---|---|---|---|---|")
        for r in review_rows:
            grade, _ = _data_quality(r.snapshot)
            state_label = r.review_state.replace("_", " ").title()
            lines.append(f"| **{r.ticker}** | {state_label} | {SEVERITY_BADGE_MD[r.severity]} | "
                         f"{r.primary_reason} | {DQ_BADGE_MD[grade]} | {r.next_action} |")
    else:
        lines.append("_No holdings flagged for review this quarter._")
    lines.append("")

    # 4. What changed since prior screen
    lines.append("## 4. What changed since prior screen")
    lines.append("")
    lines.append(f"_Compared {rd['current_date']} (current) vs. {rd['prior_date']} (prior). At a "
                 "21-day window, deltas are small by design — the format is what's being demonstrated. "
                 "Real value compounds over true quarterly cadence (next 10-K cycle)._")
    lines.append("")
    changed = [r for r in rd["ticker_reports"] if r.diff and (
        r.diff.get("metric_deltas") or r.diff.get("newly_fired") or r.diff.get("newly_cleared")
        or r.diff.get("final_classification", {}).get("previous") != r.diff.get("final_classification", {}).get("current")
    )]
    if changed:
        for r in changed:
            d = r.diff
            lines.append(f"### {r.ticker}")
            cls = d.get("final_classification", {})
            if cls.get("previous") != cls.get("current"):
                lines.append(f"- Classification: **{cls.get('previous', '?')}** → **{cls.get('current', '?')}**")
            for g in d.get("newly_fired", []):
                lines.append(f"- Gate newly fired: `{g}`")
            for g in d.get("newly_cleared", []):
                lines.append(f"- Gate newly cleared: `{g}`")
            for k, v in (d.get("metric_deltas") or {}).items():
                lines.append(f"- {k}: {v.get('previous')} → {v.get('current')}")
            lines.append("")
    else:
        lines.append("_No material changes detected at this window._")
    lines.append("")

    # 5. Per-ticker evidence scorecard
    lines.append("## 5. Per-ticker evidence scorecard")
    lines.append("")
    for r in rd["ticker_reports"]:
        s = r.snapshot
        if not s:
            lines.append(f"### {r.ticker} — _not in S&P 500 snapshot_")
            lines.append("")
            lines.append(f"- Position type: {r.position_type}")
            lines.append(f"- Thesis as written: _{r.thesis}_")
            lines.append("")
            continue
        cls = s.get("classification", "?")
        v = s.get("value_score")
        q = s.get("quality_score")
        c_score = s.get("conviction_score")
        f = s.get("piotroski_f")
        gp = s.get("gross_profitability")
        mom = s.get("momentum_12m")
        pe = s.get("pe_ratio")
        fcf_y = s.get("fcf_yield")
        ey = s.get("earnings_yield")
        sector = s.get("sector", "—")
        company = s.get("company", r.ticker)
        grade, warnings = _data_quality(s)

        gates_now = _gates_fired(s)
        gates_str = ", ".join(g.replace("_fired", "").replace("_", " ") for g in gates_now) or "none"

        lines.append(f"### {r.ticker} — {company}")
        lines.append("")
        lines.append(f"- **Sector:** {sector}  |  **Position:** {r.position_type}  |  "
                     f"**Classification:** **{cls}**")
        lines.append(f"- **Thesis as written:** _{r.thesis or '—'}_")
        lines.append(f"- **Value score:** {_fmt_num(v)}  |  **Quality score:** {_fmt_num(q)}  |  "
                     f"**Conviction:** {_fmt_num(c_score)}")
        lines.append(f"- **Piotroski F:** {f if f is not None else '—'}/9  |  "
                     f"**Gross profitability:** {_fmt_num(gp, 2) if gp is not None else '—'}")
        lines.append(f"- **Earnings yield:** {_fmt_pct(ey)}  |  **FCF yield:** {_fmt_pct(fcf_y)}  |  "
                     f"**P/E:** {_fmt_num(pe)}  |  **12m momentum:** {_fmt_pct(mom * 100 if isinstance(mom, (int, float)) else None)}")
        lines.append(f"- **Gates fired:** {gates_str}")
        lines.append(f"- **Data quality:** {DQ_BADGE_MD[grade]}"
                     + (f" — {'; '.join(warnings)}" if warnings else ""))

        if r.bear_case:
            lines.append("")
            lines.append("**Bear case:**")
            for b in r.bear_case:
                lines.append(f"- {b}")

        if r.research_checklist:
            lines.append("")
            lines.append("**Before any action, verify:**")
            for item in r.research_checklist:
                lines.append(f"- [ ] {item}")
        lines.append("")

    # 6. (Bear cases are inline above. Keeping section heading optional.)
    # 7. Data-quality warnings
    lines.append("## 6. Data-quality warnings")
    lines.append("")
    dq_list = [r for r in rd["ticker_reports"] if r.snapshot and _data_quality(r.snapshot)[0] in ("yellow", "red")]
    if dq_list:
        for r in dq_list:
            grade, warnings = _data_quality(r.snapshot)
            lines.append(f"- **{r.ticker}** ({DQ_BADGE_MD[grade]}): {'; '.join(warnings) or 'see scorecard'}")
    else:
        lines.append("_All in-universe holdings are data-quality green in this snapshot._")
    lines.append("")

    # 8. Decision journal prompt
    lines.append("## 7. Decision journal prompt")
    lines.append("")
    lines.append("For each flagged holding, write one paragraph answering:")
    lines.append("")
    lines.append("- Why do I own (or watch) this company?")
    lines.append("- What evidence would make me change my mind?")
    lines.append("- What changed since my original thesis?")
    lines.append("- Am I reacting to price movement or business evidence?")
    lines.append("- What is the next filing or event that matters?")
    lines.append("- Have I read the bear case fairly, or am I dismissing it?")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("_Sample artifact for the Assay Portfolio Doctor. Reviews public evidence; does not "
                 "predict returns. Reviewed in conjunction with primary filings and the investor's "
                 "own thesis. Not personalized financial advice._")
    lines.append("")
    return "\n".join(lines)


# ── HTML rendering ─────────────────────────────────────────────────────


SEVERITY_BADGE_HTML = {
    "high": '<span class="badge badge-high">high</span>',
    "medium": '<span class="badge badge-med">medium</span>',
    "low": '<span class="badge badge-low">low</span>',
}
DQ_BADGE_HTML = {
    "green": '<span class="dq dq-green">green</span>',
    "yellow": '<span class="dq dq-yellow">yellow</span>',
    "red": '<span class="dq dq-red">red</span>',
    "unknown": '<span class="dq dq-unknown">unknown</span>',
}


CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 760px;
       margin: 32px auto; padding: 0 20px; color: #1f2328; line-height: 1.55; }
h1 { border-bottom: 1px solid #d0d7de; padding-bottom: 8px; }
h2 { border-bottom: 1px solid #eaeef2; padding-bottom: 6px; margin-top: 36px; }
h3 { margin-top: 28px; color: #24292f; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 14px; }
th, td { border: 1px solid #d0d7de; padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #f6f8fa; font-weight: 600; }
code, pre { font-family: ui-monospace, SFMono-Regular, monospace; background: #f6f8fa;
            padding: 1px 4px; border-radius: 3px; font-size: 13px; }
blockquote { border-left: 4px solid #d0d7de; padding: 4px 14px; margin: 12px 0; color: #57606a;
             background: #f6f8fa; border-radius: 0 4px 4px 0; }
ul { padding-left: 22px; }
li { margin: 4px 0; }
.badge { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 12px;
         font-weight: 600; }
.badge-high { background: #ffebe9; color: #82071e; border: 1px solid #ff8182; }
.badge-med  { background: #fff8c5; color: #633c01; border: 1px solid #d4a72c; }
.badge-low  { background: #ddf4ff; color: #0550ae; border: 1px solid #54aeff; }
.dq { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; }
.dq-green   { background: #dafbe1; color: #1a7f37; border: 1px solid #4ac26b; }
.dq-yellow  { background: #fff8c5; color: #633c01; border: 1px solid #d4a72c; }
.dq-red     { background: #ffebe9; color: #82071e; border: 1px solid #ff8182; }
.dq-unknown { background: #eaeef2; color: #57606a; border: 1px solid #afb8c1; }
.disclaimer { color: #57606a; font-size: 14px; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 28px 0; }
.scorecard { background: #f6f8fa; padding: 12px 16px; border-radius: 6px; margin: 12px 0; }
"""


def _h(s: str) -> str:
    return html.escape(str(s) if s is not None else "")


def render_html(rd: dict) -> str:
    out = ["<!doctype html>", "<html lang='en'><head>", "<meta charset='utf-8'>",
           f"<title>Assay Portfolio Doctor — Sample Report</title>",
           "<style>", CSS, "</style></head><body>"]

    out.append("<h1>Assay Portfolio Doctor — Sample Report</h1>")
    out.append(f"<p class='disclaimer'><em>Generated {_h(rd['report_date'])} from S&amp;P 500 snapshot "
               f"dated {_h(rd['current_date'])} (prior baseline: {_h(rd['prior_date'])})</em></p>")
    out.append("<blockquote><strong>Public-data review tool. Not personalized financial advice.</strong> "
               "Review flags, not buy/sell recommendations. Minimum 3–5 year horizon. Selection alpha "
               "unproven; this report organizes evidence — it does not forecast returns.</blockquote>")

    # 1. Executive summary
    c = rd["counts"]
    out.append("<h2>1. Executive summary</h2><ul>")
    out.append(f"<li><strong>Reviewed:</strong> {_h(rd['total'])} tickers</li>")
    out.append(f"<li><strong>Sell-review flags:</strong> {_h(c.get('SELL_REVIEW', 0))}</li>")
    out.append(f"<li><strong>Monitor flags:</strong> {_h(c.get('MONITOR', 0))}</li>")
    out.append(f"<li><strong>Data-quality warnings:</strong> {_h(rd['dq_warnings'])}</li>")
    out.append(f"<li><strong>No-action holdings:</strong> {_h(c.get('NO_ACTION', 0))}</li>")
    if c.get("DATA_INSUFFICIENT"):
        out.append(f"<li><strong>Data insufficient:</strong> {_h(c['DATA_INSUFFICIENT'])}</li>")
    if c.get("NOT_IN_UNIVERSE"):
        out.append(f"<li><strong>Not in universe:</strong> {_h(c['NOT_IN_UNIVERSE'])}</li>")
    out.append("</ul>")
    out.append("<blockquote><em>Important: these are research-review flags, not buy/sell "
               "recommendations.</em></blockquote>")

    # 2. What this report won't tell you
    out.append("<h2>2. What this report won't tell you</h2><ul>")
    out.append("<li><strong>It will not predict returns.</strong> Empirical testing on this system shows "
               "selection alpha is unproven and too fragile to sell as a forecast.</li>")
    out.append("<li><strong>It will not tell you to buy or sell.</strong> Every flag is a "
               "<em>review</em> trigger, not an action.</li>")
    out.append("<li><strong>It will not factor in your personal situation.</strong> Tax basis, holding "
               "period, concentration, time horizon, liquidity needs — all yours to weigh.</li>")
    out.append("<li><strong>It will not tell you the bull case.</strong> The system is structurally "
               "skeptical; the bull case is yours to build.</li>")
    out.append("<li><strong>It will not replace reading the 10-K.</strong> The screen organizes public "
               "evidence; it does not understand the business.</li>")
    out.append("</ul>")

    # 3. Holdings requiring review
    out.append("<h2>3. Holdings requiring review</h2>")
    review_rows = [r for r in rd["ticker_reports"] if r.review_state != "NO_ACTION"]
    if review_rows:
        out.append("<table><thead><tr><th>Ticker</th><th>Review state</th><th>Severity</th>"
                   "<th>Primary reason</th><th>Data quality</th><th>Next research action</th></tr></thead><tbody>")
        for r in review_rows:
            grade, _ = _data_quality(r.snapshot)
            state_label = r.review_state.replace("_", " ").title()
            out.append(f"<tr><td><strong>{_h(r.ticker)}</strong></td><td>{_h(state_label)}</td>"
                       f"<td>{SEVERITY_BADGE_HTML[r.severity]}</td><td>{_h(r.primary_reason)}</td>"
                       f"<td>{DQ_BADGE_HTML[grade]}</td><td>{_h(r.next_action)}</td></tr>")
        out.append("</tbody></table>")
    else:
        out.append("<p><em>No holdings flagged for review this quarter.</em></p>")

    # 4. What changed
    out.append("<h2>4. What changed since prior screen</h2>")
    out.append(f"<p class='disclaimer'><em>Compared {_h(rd['current_date'])} (current) vs. "
               f"{_h(rd['prior_date'])} (prior). At a 21-day window, deltas are small by design — the "
               "format is what's being demonstrated. Real value compounds over true quarterly cadence "
               "(next 10-K cycle).</em></p>")
    changed = [r for r in rd["ticker_reports"] if r.diff and (
        r.diff.get("metric_deltas") or r.diff.get("newly_fired") or r.diff.get("newly_cleared")
        or r.diff.get("final_classification", {}).get("previous") != r.diff.get("final_classification", {}).get("current")
    )]
    if changed:
        for r in changed:
            d = r.diff
            out.append(f"<h3>{_h(r.ticker)}</h3><ul>")
            cls = d.get("final_classification", {})
            if cls.get("previous") != cls.get("current"):
                out.append(f"<li>Classification: <strong>{_h(cls.get('previous', '?'))}</strong> → "
                           f"<strong>{_h(cls.get('current', '?'))}</strong></li>")
            for g in d.get("newly_fired", []):
                out.append(f"<li>Gate newly fired: <code>{_h(g)}</code></li>")
            for g in d.get("newly_cleared", []):
                out.append(f"<li>Gate newly cleared: <code>{_h(g)}</code></li>")
            for k, v in (d.get("metric_deltas") or {}).items():
                out.append(f"<li>{_h(k)}: {_h(v.get('previous'))} → {_h(v.get('current'))}</li>")
            out.append("</ul>")
    else:
        out.append("<p><em>No material changes detected at this window.</em></p>")

    # 5. Per-ticker evidence scorecard
    out.append("<h2>5. Per-ticker evidence scorecard</h2>")
    for r in rd["ticker_reports"]:
        s = r.snapshot
        if not s:
            out.append(f"<h3>{_h(r.ticker)} — <em>not in S&amp;P 500 snapshot</em></h3>")
            out.append(f"<p>Position type: {_h(r.position_type)}</p>")
            out.append(f"<p>Thesis as written: <em>{_h(r.thesis)}</em></p>")
            continue
        cls = s.get("classification", "?")
        v = s.get("value_score"); q = s.get("quality_score"); c_score = s.get("conviction_score")
        f = s.get("piotroski_f"); gp = s.get("gross_profitability")
        mom = s.get("momentum_12m"); pe = s.get("pe_ratio"); fcf_y = s.get("fcf_yield"); ey = s.get("earnings_yield")
        sector = s.get("sector", "—"); company = s.get("company", r.ticker)
        grade, warnings = _data_quality(s)
        gates_now = _gates_fired(s)
        gates_str = ", ".join(g.replace("_fired", "").replace("_", " ") for g in gates_now) or "none"

        out.append(f"<h3>{_h(r.ticker)} — {_h(company)}</h3>")
        out.append("<div class='scorecard'>")
        out.append(f"<p><strong>Sector:</strong> {_h(sector)} &nbsp;|&nbsp; "
                   f"<strong>Position:</strong> {_h(r.position_type)} &nbsp;|&nbsp; "
                   f"<strong>Classification:</strong> <strong>{_h(cls)}</strong></p>")
        out.append(f"<p><strong>Thesis as written:</strong> <em>{_h(r.thesis or '—')}</em></p>")
        out.append("<ul>")
        out.append(f"<li>Value score: {_h(_fmt_num(v))} &nbsp;|&nbsp; "
                   f"Quality score: {_h(_fmt_num(q))} &nbsp;|&nbsp; "
                   f"Conviction: {_h(_fmt_num(c_score))}</li>")
        out.append(f"<li>Piotroski F: {_h(f if f is not None else '—')}/9 &nbsp;|&nbsp; "
                   f"Gross profitability: {_h(_fmt_num(gp, 2) if gp is not None else '—')}</li>")
        mom_pct = mom * 100 if isinstance(mom, (int, float)) else None
        out.append(f"<li>Earnings yield: {_h(_fmt_pct(ey))} &nbsp;|&nbsp; "
                   f"FCF yield: {_h(_fmt_pct(fcf_y))} &nbsp;|&nbsp; "
                   f"P/E: {_h(_fmt_num(pe))} &nbsp;|&nbsp; "
                   f"12m momentum: {_h(_fmt_pct(mom_pct))}</li>")
        out.append(f"<li>Gates fired: {_h(gates_str)}</li>")
        warning_text = (" — " + "; ".join(warnings)) if warnings else ""
        out.append(f"<li>Data quality: {DQ_BADGE_HTML[grade]}{_h(warning_text)}</li>")
        out.append("</ul>")
        out.append("</div>")

        if r.bear_case:
            out.append("<p><strong>Bear case:</strong></p><ul>")
            for b in r.bear_case:
                out.append(f"<li>{_h(b)}</li>")
            out.append("</ul>")

        if r.research_checklist:
            out.append("<p><strong>Before any action, verify:</strong></p><ul>")
            for item in r.research_checklist:
                out.append(f"<li>☐ {_h(item)}</li>")
            out.append("</ul>")

    # 6. Data-quality warnings
    out.append("<h2>6. Data-quality warnings</h2>")
    dq_list = [r for r in rd["ticker_reports"] if r.snapshot and _data_quality(r.snapshot)[0] in ("yellow", "red")]
    if dq_list:
        out.append("<ul>")
        for r in dq_list:
            grade, warnings = _data_quality(r.snapshot)
            out.append(f"<li><strong>{_h(r.ticker)}</strong> ({DQ_BADGE_HTML[grade]}): "
                       f"{_h('; '.join(warnings) or 'see scorecard')}</li>")
        out.append("</ul>")
    else:
        out.append("<p><em>All in-universe holdings are data-quality green in this snapshot.</em></p>")

    # 7. Decision journal prompt
    out.append("<h2>7. Decision journal prompt</h2>")
    out.append("<p>For each flagged holding, write one paragraph answering:</p><ul>")
    for q in [
        "Why do I own (or watch) this company?",
        "What evidence would make me change my mind?",
        "What changed since my original thesis?",
        "Am I reacting to price movement or business evidence?",
        "What is the next filing or event that matters?",
        "Have I read the bear case fairly, or am I dismissing it?",
    ]:
        out.append(f"<li>{_h(q)}</li>")
    out.append("</ul>")

    out.append("<hr>")
    out.append("<p class='disclaimer'><em>Sample artifact for the Assay Portfolio Doctor. Reviews "
               "public evidence; does not predict returns. Reviewed in conjunction with primary filings "
               "and the investor's own thesis. Not personalized financial advice.</em></p>")
    out.append("</body></html>")
    return "\n".join(out)


# ── Main ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portfolio", default=str(EXAMPLES_DIR / "sample_portfolio.csv"),
                        help="Path to portfolio CSV")
    parser.add_argument("--current", default=None, help="Path to current screen JSON (defaults to latest)")
    parser.add_argument("--prior", default=None, help="Path to prior screen JSON (defaults to second-latest)")
    parser.add_argument("--out-md", default=str(EXAMPLES_DIR / "portfolio_doctor_sample.md"))
    parser.add_argument("--out-html", default=str(EXAMPLES_DIR / "portfolio_doctor_sample.html"))
    parser.add_argument("--bear-overrides", default=str(EXAMPLES_DIR / "bear_case_overrides.json"),
                        help="Optional JSON of per-ticker hand-polished bear cases")
    args = parser.parse_args()

    portfolio_path = Path(args.portfolio)
    if not portfolio_path.exists():
        print(f"Portfolio CSV not found: {portfolio_path}", file=sys.stderr)
        return 2

    if args.current and args.prior:
        current_path = Path(args.current)
        prior_path = Path(args.prior)
    else:
        screens = find_full_screens()
        if len(screens) < 2:
            print(f"Need at least 2 full screen JSONs in {RESULTS_DIR}", file=sys.stderr)
            return 2
        current_path = Path(args.current) if args.current else screens[0]
        prior_path = Path(args.prior) if args.prior else screens[-1]  # oldest available for max spacing

    portfolio = load_portfolio(portfolio_path)
    current_stocks = _load_stocks(current_path)
    prior_stocks = _load_stocks(prior_path)
    current_date = current_path.stem.replace("screen_", "")
    prior_date = prior_path.stem.replace("screen_", "")

    overrides = None
    overrides_path = Path(args.bear_overrides)
    if overrides_path.exists():
        with open(overrides_path, encoding="utf-8") as f:
            raw = json.load(f)
        # Drop the _README key if present.
        overrides = {k: v for k, v in raw.items() if not k.startswith("_")}

    rd = build_report_data(portfolio, current_stocks, prior_stocks, current_date, prior_date,
                           bear_case_overrides=overrides)

    md = render_markdown(rd)
    Path(args.out_md).write_text(md, encoding="utf-8")
    print(f"Wrote Markdown: {args.out_md}")

    html_doc = render_html(rd)
    Path(args.out_html).write_text(html_doc, encoding="utf-8")
    print(f"Wrote HTML: {args.out_html}")

    print(f"\nUsing current={current_date}, prior={prior_date}")
    print(f"Counts: {rd['counts']}, DQ warnings: {rd['dq_warnings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

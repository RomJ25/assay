# Portfolio Doctor — Validation Log

Track the manual paid-validation push here. Goal: 5 prospects, ≥2 paying customers, ≥3 sending portfolio CSVs.

**Pre-committed success thresholds** (decided before any outreach — don't move the goalposts):

| Signal | Pass condition |
|---|---:|
| Prospects sending a portfolio/watchlist | 3 / 5 |
| Prospects paying anything | 2 / 5 |
| Prospects paying $49+ | 2 / 5 |
| Prospects asking for quarterly cadence | 1 / 5 |
| Prospects preferring report over dashboard | majority of payers |

If thresholds met: build Sprint 1 (real `portfolio/importer.py`, `portfolio/doctor.py`,
`discipline/sell_rules.py`, `research/packet.py`).

If thresholds **not** met: do not build Sprint 1. Re-examine: was the price wrong, the format
wrong, the audience wrong, or the value wrong? Each implies a different next move.

---

## Outreach ledger

Replace the placeholder rows with real outreach. Use initials only or generic descriptors
("VC analyst friend," "ex-colleague who runs personal IRA") to keep the file commit-safe.

| # | Initials / role | Date sent | Response | Sent CSV? | Paid? | Price | Notes |
|---|---|---|---|---|---|---|---|
| 1 | _e.g. R.L. (PM friend)_ | YYYY-MM-DD | — | — | — | — | — |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |

---

## Per-customer feedback notes

For each delivered report, capture the answers to the 8 feedback questions from `README.md`. One
section per customer. Keep it short — the value is in the patterns across customers, not in any
single response.

### Customer 1 — _initials_

- Date delivered:
- Tickers reviewed:
- Q1 (Would this have helped with a real holding?):
- Q2 (Most valuable section?):
- Q3 (Noise section?):
- Q4 (Pay for own portfolio?):
- Q5 (Price?):
- Q6 (Cadence — quarterly / ad-hoc / filing-driven?):
- Q7 (Trust the data?):
- Q8 (What would make it trustworthy enough to act on?):
- Free-form takeaway:

### Customer 2 — _initials_

(repeat as above)

---

## Patterns across customers (fill in after 3+ deliveries)

Look for:

- **Section unanimity:** which section was rated #1 most-valuable by ≥2 customers? (That's the
  load-bearing section. Consider doubling down on it in Sprint 1.)
- **Section divergence:** which section was rated noise by ≥2 customers? (That's the cut
  candidate. Don't ship it in Sprint 1 unless someone explicitly defended it.)
- **Trust failures:** what did the same 2+ customers say would make the data more trustworthy?
  (That's the data-quality bar — likely involves SEC live or filing-date provenance UI.)
- **Cadence preference:** quarterly vs. filing-driven vs. ad-hoc. The one with majority votes is
  the SaaS rhythm. (Quarterly is the easy default; filing-driven is the right answer if 2+ ask.)

---

## Decision date

Pre-commit a date by which you'll decide go/no-go on Sprint 1, regardless of how many responses
you have. Long open-ended validation phases drift.

**Decision date: YYYY-MM-DD**

If by that date you have ≥2 paid: build Sprint 1.
If not: write up what you learned, decide whether to pivot the offer (different audience, different
artifact, different price), and either re-run the test or stop building.

The point of a pre-committed decision date is to make the answer to "should I keep going?"
empirical, not emotional.

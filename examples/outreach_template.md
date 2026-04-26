# Outreach templates — Portfolio Doctor manual validation

Use these when contacting 5 prospects from your network. Replace `[NAME]`, `[CONTEXT]`, and the
`[OFFER LINK]` placeholders. The goal is **one paid report per prospect** — the question being
answered is "is the artifact worth $49 of someone's actual money," not "is it free interesting."

## Pre-conditions for a good prospect

- They actually invest (paper portfolios don't count for this validation).
- They've talked to you about a holding within the past 6 months — i.e., investing is part of how
  they spend mental energy.
- They have at least 5 individual stock positions (not just index funds).
- You have an existing relationship — cold outreach is a different test, run that separately if
  you want, but **start with people whose response you can read clearly**.

5 strong candidates beat 20 weak ones. Filter ruthlessly.

---

## Email version (for prospects who prefer email)

**Subject:** A second pair of eyes on your portfolio — public-data review

Hey [NAME],

Quick context: I built a public-data screening tool over the last several months that organizes
evidence on S&P 500 companies — accounting-quality scores (Piotroski F), valuation, momentum,
filing-date provenance — and surfaces "review" flags when a holding's evidence weakens between
filings.

The thing it produces is **not** a buy/sell recommendation and **not** a forecast. It's a
disciplined evidence summary plus a written bear case for each holding, designed to make sure
nothing slips past you between 10-Q cycles. I've attached a sample report for a fictional
10-stock portfolio so you can see the format.

If it would be useful for any real holdings of yours, I'm running a manual offer:

- Send me a CSV (ticker, position type, your one-line thesis, optional review date)
- I run the report
- You get back a Markdown + HTML version within 3 business days
- $49 for up to 5 tickers, $99 for up to 15, $249 for up to 50

This is a validation push — I'm trying to find out whether the artifact is worth real money before
I build infrastructure around it. Honest "no" is more useful to me than polite "maybe."

Sample is at: [LINK or attach the .html file]

— [YOUR NAME]

---

## DM/text version (for prospects you message casually)

> Made a thing. Public-data portfolio review tool — not a stock picker, more like a structured
> evidence summary + bear case per holding to catch what's slipping between filings.
> Sample report: [LINK]
> If you want one for any real holdings, $49 for up to 5 tickers, 3-day turnaround. No
> recommendations, just the evidence and what's deteriorating. Curious if it's actually useful or
> if the format is wrong.

Send the sample link first. If they reply with interest, send the offer. If they reply with
"looks interesting" but don't follow up, that's a soft signal — not a paying customer yet.

---

## Substack/X broadcast version (only after 2+ paying customers)

Don't broadcast until at least 2 of the first 5 paid. A broadcast push without that signal turns
this into "asking strangers to validate something my friends wouldn't pay for" — which is a much
weaker test. Broadcast format only when the network test has converted.

---

## What to actually charge

Stripe / Venmo / direct bank transfer are all fine for the validation phase. **Take real money,
not "I'll buy you coffee."** The friction of real payment is the entire point — it's the only
thing that distinguishes "polite interest" from "real demand."

Refund anyone who asks. Better to refund 5/5 than to spend a week rationalizing why you should
have charged.

## What to do after each delivery

Run through the 8 questions in `examples/README.md` § "Feedback questions to ask every paying
user." Even with a $49 customer, this is the most valuable artifact you'll get out of the
exchange — a real read on what to keep, what to cut, and whether to build Sprint 1.

Track responses in `examples/validation_log.md`.

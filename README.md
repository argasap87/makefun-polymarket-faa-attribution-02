# polymarket-faa-attribution-02 — improved entry (local build, NOT submitted)

Forecasts each market's Yes price 240 minutes ahead, 5 quantiles
[0.05, 0.25, 0.5, 0.75, 0.95], as `q_tau(h) = clamp(x + z_tau * sigma * sqrt(h), 0, 1)`
where `x` is the last price and `sigma` is estimated per market from its own
recent moves:

- **sigma** = clip(0.9 × RMS of the last 60 one-minute price changes,
  winsorized at ±0.02, 0.0003, 0.004)
- **median** = last price (martingale, no drift)

Node 22, stdlib only, no network, deterministic. Run like the grader:
`MAKEFUN_INPUT_DIR=<input> MAKEFUN_OUTPUT_DIR=<out> node main.ts`
(~0.3 s for all six practice cases; outputs ≤ 242 KB, limit 1 MiB).

## Practice evaluation (p00–p05, mean pinball loss ×100)

Realized prices: p00–p04 from the next case's file (cases are 4 h apart,
horizon is exactly 240 min); p05 fetched from Polymarket's public
`prices-history` API (the house scores practice through 2026-11-13T06:00Z).
The evaluator reproduces the house baseline's reported practice loss
exactly (0.363589), so the comparison is on the same ground truth.

| case | this entry | house baseline (sigma 0.0025) |
|------|-----------|-------------------------------|
| p00  | 0.512142  | 0.536138 |
| p01  | 0.309039  | 0.380352 |
| p02  | 0.327710  | 0.408408 |
| p03  | 0.257055  | 0.368599 |
| p04  | 0.206527  | 0.298794 |
| p05  | 0.118756  | 0.238232 |
| **ALL** | **0.277719** | **0.363589** |

**−23.6% vs baseline.** Median error is identical (0.7675 — same median),
the gain is all in the spread: 90% coverage 0.875 (honest ≈ 0.90) vs the
baseline's 0.950 (over-wide). Beats baseline in every case.

## What was tested and rejected (same evaluator)

- Fixed sigma 0.001 / 0.0012: 0.327 / 0.329 — per-market vol matters.
- Longer vol windows (240/1440 min): 0.286 / worse — stale jumps pollute it.
- Student-t outer quantiles (df 3/5): 0.286 / 0.283 — worse.
- Drift from the last 240 min (×0.25 / ×0.5): 0.314 / 0.350 — trend chasing fails.
- Mean-reversion (drift ×−0.25): 0.450, p03 = 1.155 — catastrophic.
- Level scaling sigma ∝ √(x(1−x)): 0.283 — worse.
- Horizon exponent 0.55 / 0.6: 0.284 / 0.299 — worse.
- W=30 / mult 0.8 scored 0.275, W=45 / 0.85 scored 0.275 — within ~1% of
  this choice; W=60 / 0.9 was kept as the robust middle of that plateau,
  not a tuned edge.

## Caveats

- The practice is the NVIDIA CEO event, not the final FAA markets; the
  rules warn its score is no guide to the final. The final has only
  4 markets and is jumpier (Iran 0.49 → 0.275 in one minute). This entry
  adapts per market, but a single jump still dominates any 240-min window.
- `eval/` holds the local evaluation scripts and the fetched p05 realized
  prices; it is not part of the entry. The entry itself is only
  `main.ts` + `LICENSE`. No GitHub repo was created and nothing was
  submitted to make.fun.

## Files

- `main.ts` — the entry
- `LICENSE` — MIT, copied from the kit's starter
- `README.md` — this note
- `eval/` — `eval.py` (realized prices + pinball scorer, reproduces the
  house baseline 0.363589), `grid.py`/`grid2.py`/`grid3.py` (parameter
  searches), `score_out.py` (scores a directory of `.out` files),
  `p05-realized.json` (fetched realized prices for p05)

// polymarket-faa-attribution-02 entry: per-market realized-volatility persistence.
// Based on the house baseline (starter/main.ts) but with a spread estimated from
// each market's own recent price moves instead of the fixed 0.0025:
//
//   q_tau(h) = clamp(x + z_tau * sigma * sqrt(h), 0, 1), rounded to 6 decimals
//
// where x is the market's last price (the median is a martingale: no drift —
// trend extrapolation and mean-reversion both scored *worse* than persistence
// on the practice cases, the latter catastrophically so on p03), and
//
//   sigma = clip(0.9 * RMS of the last 60 one-minute price changes,
//                 winsorized at +/-0.02, 0.0003, 0.004)
//
// Why these choices (measured on the six practice cases, p00..p05, scored
// against the realized prices — p00..p04 from the next case's file, p05
// fetched from Polymarket's public price history; the evaluator reproduces
// the house baseline's reported practice loss of 0.363589 exactly):
//   - The baseline's fixed sigma 0.0025 is far too wide for these prices:
//     88% of one-minute moves are exactly 0, the typical non-zero tick is
//     0.005-0.01, and the mean |price 240 min out - price now| is only
//     ~0.006-0.018. Its 90% coverage on practice is 0.95 (over-wide).
//   - A per-market sigma from the last 60 minutes adapts to quiet markets
//     (sigma hits the 0.0003 floor) and to live ones, while the 0.004 cap
//     stops one jump from blowing the spread up for hours. Longer windows
//     (240/1440 min) scored worse: they drag in stale jumps. Shorter
//     windows (30 min) and multipliers 0.8-1.0 all scored within ~1% of
//     this choice, so 60 min / 0.9 sits in the middle of that plateau
//     rather than at a tuned edge — the final's four FAA markets are a
//     different, jumpier regime (e.g. Iran 0.49 -> 0.275 in one minute),
//     so a robust middle beats a practice-tuned extreme.
//   - Student-t widening of the outer quantiles, level scaling
//     (sigma ~ sqrt(x(1-x))), drift, and horizon exponents above 0.5
//     were all tested and all scored worse than this plain form.
//   - The floor matters: markets whose last 60 minutes did not move at
//     all (sigma_hat = 0) still need a non-zero spread, because a jump
//     can always arrive; the cap matters symmetrically.
//
// Node 22, standard library only, no network, deterministic: the only
// inputs are the case file's prices, and every operation is a fixed
// arithmetic pass over them.

import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const INPUT_DIR = process.env.MAKEFUN_INPUT_DIR ?? '/input';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

/** The quantile levels the contest scores, in the order each row lists them. */
const QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95];
/** The standard normal's quantile at each level, to 6 decimals. */
const Z = [-1.644854, -0.67449, 0, 0.67449, 1.644854];

/** One-minute price changes older than this are ignored for the vol estimate. */
const VOL_WINDOW_MINUTES = 60;
/** One-minute changes are winsorized to this magnitude before the RMS. */
const WINSORIZE = 0.02;
/** Multiplier on the winsorized RMS (0.8-1.0 all scored within ~1%). */
const SIGMA_MULTIPLIER = 0.9;
/** Sigma floor / cap, in price units per square-root minute. */
const SIGMA_FLOOR = 0.0003;
const SIGMA_CAP = 0.004;

interface CaseMarket {
  id: string;
  prices: number[];
}

interface Case {
  horizon_minutes: number;
  quantiles: number[];
  markets: CaseMarket[];
}

/** x clamped to [0,1] and rounded to 6 decimals (0, never -0). */
const price6 = (x: number): number => Math.round(Math.min(1, Math.max(0, x)) * 1e6) / 1e6 + 0;

/**
 * Per-market sigma: RMS of the winsorized one-minute changes over the
 * last VOL_WINDOW_MINUTES minutes, scaled and clipped to [floor, cap].
 * A market with fewer than 2 prices, or no movement at all, gets the floor.
 */
function sigmaOf(prices: number[]): number {
  const n = prices.length;
  if (n < 2) return SIGMA_FLOOR;
  const w = Math.min(VOL_WINDOW_MINUTES, n - 1);
  let sumSq = 0;
  for (let i = n - 1 - w; i < n - 1; i++) {
    const d = prices[i + 1] as number - (prices[i] as number);
    const wd = Math.max(-WINSORIZE, Math.min(WINSORIZE, d));
    sumSq += wd * wd;
  }
  const rms = Math.sqrt(sumSq / w);
  return Math.min(SIGMA_CAP, Math.max(SIGMA_FLOOR, SIGMA_MULTIPLIER * rms));
}

/** The forecast of one market: horizon rows of the five quantiles around its last price. */
function forecast(m: CaseMarket, horizon: number): number[][] {
  if (m.prices.length === 0) throw new Error(`market ${m.id} has no prices`);
  const x = m.prices[m.prices.length - 1] as number;
  const sigma = sigmaOf(m.prices);
  const rows: number[][] = [];
  for (let h = 1; h <= horizon; h++) {
    const spread = sigma * Math.sqrt(h);
    rows.push(Z.map((z) => price6(x + z * spread)));
  }
  return rows;
}

mkdirSync(OUTPUT_DIR, { recursive: true });
// Every case file, in name order, so two runs write the same bytes.
const inputs = readdirSync(INPUT_DIR).filter((f) => f.endsWith('.in')).sort();
for (const file of inputs) {
  const id = file.slice(0, -'.in'.length);
  const c = JSON.parse(readFileSync(join(INPUT_DIR, file), 'utf8')) as Case;
  if (c.quantiles.length !== QUANTILES.length || c.quantiles.some((t, j) => t !== QUANTILES[j])) throw new Error(`${file} asks for quantiles ${JSON.stringify(c.quantiles)}, not ${JSON.stringify(QUANTILES)}`);
  const forecasts = c.markets.map((m) => ({ id: m.id, q: forecast(m, c.horizon_minutes) }));
  writeFileSync(join(OUTPUT_DIR, `${id}.out`), `${JSON.stringify({ forecasts })}\n`);
}

# APEX State Engine — The Math, in Plain Language

This page explains every formula the engine uses, the bug that was fixed in v2.1, and the
numbers the harness actually produces. Every number below was reproduced by running
`apex_decay_harness-v2.py` (the `ApexDecayHarnessV2` class) on 2026-10-14.

## 1. Inputs

Each conversation turn supplies four numbers, each in [0, 1]:

| Symbol | Meaning (as used in the code) |
|---|---|
| T | Trust |
| V | Validation / warmth |
| E | Entropy / volatility of the exchange |
| A | Adversarial pressure |

## 2. The pipeline, step by step

**Step 1 — raw stability**

    S_raw = (T * V) / (E^2 + A + 1.0)

The `+1.0` keeps the denominator from getting tiny. (The old version used `+0.01`, which let
small inputs explode — e.g. a "resting stranger" T=0.1, V=0.5, E=0, A=0 scored 5.0.)
Because the denominator is at least 1, S_raw is never above T*V ≤ 1.

**Step 2 — target**

    s_target = min(1.0, S_raw * 1.15)

**Step 3 — slow drift toward the target (exponential moving average)**

    S_mod(t) = s_target * (1 - e^(-λ)) + S_mod(t-1) * e^(-λ),   base λ = 0.035

Each turn S_mod closes about 3.4% of the gap to s_target. One exception: if E > 0.80 and
V < 0.20 (acute shock), S_mod is set straight to 0.

**Step 4 — trauma slows recovery (optional, on by default)**

- If E > 0.75 and V < 0.25: `trauma += (0.25 - min(0.25, S_raw)) * 0.15`, capped at 0.90.
- Else if E < 0.20 and V > 0.85: `trauma -= 0.015` (floor 0).
- `λ_eff = max(0.005, 0.035 * (1 - trauma))`

Higher trauma → smaller λ → slower drift back up.

**Step 5 — squash to a 0–1 "smooth" score**

    S_smooth = 1 / (1 + e^(-8 * (S_mod - 0.5)))

**Step 6 — pick a mode (node), with hysteresis**

| Condition | Node |
|---|---|
| S_smooth < 0.32 | GUT (and the "locked" flag is set) |
| 0.32 ≤ S_smooth ≤ 0.35 | keep the previous mode (deadband) |
| 0.35 < S_smooth ≤ 0.78 | HEAD |
| S_smooth > 0.78 | HEART |

The deadband stops the mode from flickering when the score hovers near the boundary.

Inverting the sigmoid gives the same thresholds in S_mod terms:

| S_smooth threshold | Equivalent S_mod |
|---|---|
| 0.32 (lock into GUT) | 0.5 + ln(0.32/0.68)/8 ≈ **0.4058** |
| 0.35 (escape GUT)    | 0.5 + ln(0.35/0.65)/8 ≈ **0.4226** |
| 0.78 (enter HEART)   | 0.5 + ln(0.78/0.22)/8 ≈ **0.6582** |

## 3. The old 0.147 bug and the fix

Before v2.1 the code used `s_target = S_raw * 0.147` (a leftover from the old 0.01 denominator).
With the 1.0 denominator, S_raw ≤ 1, so s_target ≤ 0.147, so S_mod can never exceed 0.147, so

    S_smooth ≤ 1 / (1 + e^(-8 * (0.147 - 0.5))) ≈ 0.056

That is far below the 0.35 escape threshold: **once in GUT, the engine could never leave**,
no matter how kind the inputs. v2.1 replaces it with `s_target = min(1.0, S_raw * 1.15)`.

## 4. Closed-form escape time

If the inputs (and therefore s_target and λ) stay constant, the EMA has an exact solution:

    S_mod(n) = s_target - (s_target - S_mod(0)) * e^(-λ n)

Setting S_mod(n) equal to a threshold s* and solving for n:

    N_escape = ln( (s_target - S_mod(0)) / (s_target - s*) ) / λ

Use s* ≈ 0.4226 to leave GUT, s* ≈ 0.6582 to reach HEART. The actual turn is the first
whole turn after N_escape.

**Critical value.** S_mod can only approach s_target, never pass it. So escape from GUT is only
possible if **s_target > 0.4226** (equivalently S_raw > 0.4226/1.15 ≈ 0.3675). Below that, the
engine stays in GUT forever, however long you wait. Reaching HEART needs s_target > 0.6582.

## 5. Measured numbers (ACUTE_BETRAYAL_REPAIR, extended to 100 turns)

Scenario: turns 0–10 calm (T .85, V .80, E .20, A .05); turns 11–20 shock (T .85, V 0, E .90,
A .50); turns 21–40 repair with E falling linearly from 0.90 to 0.20 (V .95, A .05); turns
41–100 held calm at the turn-40 inputs (T .85, V .95, E .20, A .05), giving
S_raw ≈ 0.7408 and s_target ≈ 0.8519.

| | No trauma (`--disable-trauma`) | With trauma (default) |
|---|---|---|
| Turn 10 S_smooth (HEART) | 0.964 | 0.964 |
| Turn 11 S_smooth (shock) | 0.018 | 0.018 |
| Trauma load after shock | 0 | 0.375 |
| λ_eff during recovery | 0.035 | 0.02188 |
| Turn 40 S_mod / S_smooth | 0.355 / 0.239 (GUT) | 0.247 / 0.117 (GUT) |
| **Leaves GUT** | **turn 45** | **turn 56** |
| **Reaches HEART** | **turn 67** | **turn 93** |

Closed form starting from turn 40 agrees: no trauma N ≈ 4.2 → turn 45 and N ≈ 26.9 → turn 67;
with trauma N ≈ 15.7 → turn 56 and N ≈ 52.0 → turn 93.

(The 40-turn scenario on its own ends in GUT in both cases — the repair window is too short.)

## 6. Honest limitations

- **Trauma never heals in this scenario.** The unburden rule needs E < 0.20 strictly, but the
  repair phase ends at E = 0.20 and the calm phase holds it there. So trauma stays at 0.375
  forever and λ stays at 0.02188. This is a known limitation, not a design claim.
  (At turn 40, E is actually 0.20000000000000007 due to floating-point rounding — still not < 0.20.)
- **The numbers depend on hand-picked constants** (1.15 gain, λ = 0.035, the 8 in the sigmoid,
  0.32/0.35/0.78 thresholds, trauma increments). None were fitted to human or model data.
- **The shock override is a hard reset** (S_mod = 0), so recovery time doesn't depend on how
  stable the engine was before the shock.
- **Hysteresis is only in S_smooth space**; the HEAD/HEART boundary at 0.78 has no deadband.
- **This is a deterministic toy dynamical system.** Words like "trauma", "allostasis" and
  "somatic" are analogies; the code doesn't model biology, and nothing here shows that it
  changes the behavior of any language model. That would need separate experiments.

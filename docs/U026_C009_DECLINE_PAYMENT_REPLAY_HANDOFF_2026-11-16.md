# U026-C009 five-phase handoff — 2026-11-16

Decision: **REVISE**. No promotion or ecological improvement claim.

## I — Baseline and hypothesis
Read the current Development implementation and C008 handoff. `decide_offer` permitted a non-null `payment_lot` on both new declines and declined replay, although refusal must never carry physical payment. Hypothesis: fail-closed validation eliminates contradictory decision payloads without changing Book transfers or voluntary choice. Control: plain decline/replay remains valid, including after recipient death. Falsifier: payment-bearing decline changes state or accepted/declined historical replay breaks.

## II — Executable source
- `2def76ca60781461f00af1c2220e39836b0d6e79`: `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_exchange.py`, decline payload guards.
- `4dec7c61261a540243a628e49972db5221647a68`: `Founders_CIV_CoreCompletion151/source/world023024/tests/test_c020_resource_agreements.py`, seed 826 regression checking zero mutation, no payment on replay and replay after death.
- No second Book, time/energy currency, native WorldBox writes or changes to 100 Founder identities.

## III — RUN_MANIFEST
Branch: Development. Exact test source commit: `4dec7c61261a540243a628e49972db5221647a68`.
Focused test: NOT EXECUTED. Full Python regression: NOT EXECUTED. Conservation/checkpoint: NOT EXECUTED on C009. Matched arms/seeds/horizons: NOT EXECUTED. Seed 826 is a test fixture, not a run result. Source fingerprints: STALE, must be refreshed from actual source bytes and approved by fail-closed audit. No PR workflow run reported at inspection for test commit.
Reproduce from a clean checkout:
```sh
python tools/u026_g2_exact_source_audit.py
cd Founders_CIV_CoreCompletion151/source/world023024
PYTHONPATH=. python -m pytest -q tests/test_c020_resource_agreements.py
PYTHONPATH=. python -m pytest -q tests
```
Then execute matched G1 acceptance and checkpoint replay and preserve raw logs/Book audit.

## IV — Decision
REVISE. Functional input-validation correction only; no ecological stability or WorldBox evidence.

## V — Branch reconciliation
At audit start Development was 185 commits ahead, 0 behind Core/Integration/Outer, and 185 ahead, 1 behind main. Base SHA for Core/Integration/Outer: c935c9a7066d6fe8d122a46edd2d8ce223343be2; main: 26a02ba50a53770b14eae0368315ea01036d0b3c. Two new Development source/test commits were added; no merges. PR #3 remains draft. G0/G1 historical Development acceptance only; G2/G3 current-source promotion blocked, G4 unverified, WB-PKG/G5+ blocked.
Next assignment: exact-source fingerprint and passing full CI, then World-qualified lot identity and integrated ingestion/digestion/replay tests. Preserve P1-09 native identity reconciliation, P1-10 independent virtual Worlds, P2-11 gated opt-in WorldBox gameplay, and P2-12 CIV-OS research.

# U026-C020 eight-phase experimental integration audit (2026-11-15)

Status: REVISE. No Core/Integration/main promotion. This is a reproducible LOCAL working-tree experiment, NOT a GitHub-verified complete-source release.

1. Baseline: recovered C004 canonical source SHA256 cb3359fb9570eed1d720f14e61dfdffe7d5ecbb683a93a6191c0809ef54e5c0b; 169 baseline tests previously passed.
2. Dependency audit: Development contains separately committed C015 nutrition, C016 recovery and C017 Tree agency; complete canonical source is not committed there.
3. Implementation: local opt-in integration of C017 into IntegratedWorld._proposals/_do; controls default off. The first attempt incorrectly filtered all seed actions, including unrelated creations.
4. Regression: 172 local tests run (169 existing + 3 new), 170 pass and 2 provenance/fingerprint tests fail closed because world_integration.py changed without reviewed signature approval. Do not weaken these gates.
5. Matched simulation: 30 days, seeds 820/821/822. Control Tree counts 3/1/3; initial agency 1/1/1; revised proposal filter 3/1/3. No successful fruit-funded seeds in these short runs; zero proven ecological improvement.
6. Causal decision: preserve unrelated seed creation; investigate why fruit-funded World creation never reaches a completed transaction. No promotion.
7. Branch gate: retain Development as experimental; do not merge PR #3 or modify Core, Integration, Outer, main. C015/C016 remain unwired in this experiment. No native WorldBox testing.
8. Handoff: rerun from sanitized C020 local source package, resolve reviewed drift through provenance approval, add end-to-end seed funding/plant tests, then publish complete source and verify fresh checkout.

GitHub document commit verifies this audit only. It does not imply the local source overlay was uploaded or tested by GitHub Actions.

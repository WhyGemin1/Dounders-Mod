# U026-C016 — Five-phase implementation handoff (2026-11-16)

Decision: **REVISE**. Development-only executable mechanics change; no promotion.

## I — Baseline, hypothesis and control
Reviewed current Development `founder_exchange.py`, its existing tests, the C015 provenance candidate and all five branch ancestries. Core, Integration and Outer share `c935c9a7066d6fe8d122a46edd2d8ce223343be2`; main has a separate release commit. Hypothesis: a Founder must not propose an agreement to itself, even if the social-contact layer accidentally reports self-contact. Falsifier: self-dealing remains possible or legitimate two-Founder exchanges regress. Control: existing C020 gift/barter tests and unchanged Book balances.

## II — Actual source implementation
- `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_exchange.py`: reject `seller == receiver` with `ValueError('resource agreement requires distinct Founders')` before replay/ownership/contact checks. Commit `83f71da1f1bf7bae351d8e5cf20677593276b336`.
- `Founders_CIV_CoreCompletion151/source/world023024/tests/test_c020_resource_agreements.py`: seed 827 negative regression, asserting no Book/event/offers mutation. Commit `882a3ab34c648e72c5f77f94ce1bef84ef02e364`.
- Exact-source 516-file candidate fingerprint updated for both changed files, with no audit relaxation. Commit `b4bdb0226e3e78de9a170050f6830dbed88a8bed`. SHA256 hashes: source `9d8e34548e2b115e24b744116e65b647cef8fa452a95d3695bc3508d60893c99`; test `a32d19ce5bbad3f6fca94cb4303b282780daf2be0eac340475ce4f2534266acc`. Hash implementation checked against SHA256('abc'). Rollback: reviewed revert of the three commits, never force-push.

## III — RUN_MANIFEST
Source branch: Development; candidate commit: `b4bdb0226e3e78de9a170050f6830dbed88a8bed`; fixture seed 827; arm self-offer rejection; horizon N/A (unit regression); **execution NOT YET VERIFIED**. Current GitHub Actions queued when inspected: Core151 `43928685243`, WorldBox offline `43928685311`. No new ecological seeds, checkpoint replay, conservation acceptance or population metrics. GitHub checkout from this runtime failed DNS resolution. Reproduce: `python tools/u026_g2_exact_source_audit.py` and `cd Founders_CIV_CoreCompletion151/source/world023024 && PYTHONPATH=. python -m pytest -q tests`; additionally execute negative tamper and unlisted-source controls, G1 matched acceptance and replay checks.

## IV — Ecological analysis
The change removes a loophole for false social agreements; it does not prove Tree survival, resource competition, nutrition, juvenile recruitment or predator stability improvements. Keep 100 stable Founders, one authoritative Book, separate matter/chemical energy/fictional CE, voluntary actions and native WorldBox authority.

## V — Reconciliation and next assignment
Development was 199 commits ahead of Core after the three code/test/fingerprint commits; Core, Integration, Outer and main unchanged. PR #3 stays draft; no merge or promotion. G0/G1 historical Development evidence only; G2 candidate pending current-source CI; G3/G4 unpromoted; WB-PKG not live-verified; G5+ blocked. Next: verify C016 CI, then implement World-qualified lot identities at WORLD-024 production and Book paths, covering harvest, trade, digestion, two independent Worlds, shared scheduler and checkpoint replay. Keep native epoch reconciliation, Outer Windows package and copied-save gameplay in gated queue.

# U026-C012 — Cross-World harvest collision guard (2026-11-16)

Decision: **REVISE; do not promote.** This cycle changed executable Core151 Founder harvesting behavior on the existing Development branch. No second Book, scheduler, or WorldBox native write was introduced.

## I. Baseline and falsifier
Development was 190 commits ahead of Core/Integration/Outer, one behind main, before this cycle. The shared `_origin` resolver in `founder_exchange.py` rejects a local lot name present in two Worlds, but `perform_harvest` previously transferred directly from the selected Tree without checking that global ambiguity. Portable holdings and harvest receipts still identify the lot without World qualification. Hypothesis: rejecting ambiguous harvest before any Book transfer prevents cross-World identity aliasing. Falsifier: duplicate local IDs produce a harvest receipt, resource mutation, or event; control: a unique lot still transfers.

## II. Executable implementation
- Source: `Founders_CIV_CoreCompletion151/source/world023024/founders_civ/core/founder_harvesting.py`; commit `22fad26717243f0d8ad7eecc306ecc8d41e18244`; Git blob `3bece313e369073e0d5c033887ede7101e347445`.
- Added a pre-transfer check using existing shared `founder_exchange._origin`. Rejects ambiguous/unprovenanced local food or fruit IDs, without touching Book balances or Founder state.
- Regression: `tests/test_u026_c012_cross_world_harvest.py`; commit `47273a169fb5e6643098e653ee6f29fd8e5a7a5e`. Covers duplicate World lot rejection before transfer and a unique-lot control.
- Rollback: revert these two commits in a reviewed Development-only change, preserving history. Do not revert unrelated revisions.

## III. RUN_MANIFEST
Repository: WhyGemin1/Dounders-Mod. Branch: Development. Source commit: 22fad26717243f0d8ad7eecc306ecc8d41e18244. Test commit: 47273a169fb5e6643098e653ee6f29fd8e5a7a5e. Test seeds: none. Arms/horizons: none. Local full checkout unavailable (GitHub DNS resolution failed); **no new test is claimed passing**. CI at test commit: Core151 run 43889157348 queued; offline WorldBox run 43889157851 in progress when inspected. Source fingerprint manifest not refreshed for this new revision, so the fail-closed gate is expected to require reconciliation. No new conservation/replay/ecological result is claimed.

Reproduce from exact GitHub source:
```sh
cd Founders_CIV_CoreCompletion151/source/world023024
PYTHONPATH=. python -m pytest -q tests/test_u026_c012_cross_world_harvest.py
PYTHONPATH=. python -m pytest -q tests
cd ../../..
python tools/u026_g2_exact_source_audit.py
```
Run negative drift probes, Book audit and deterministic checkpoint replay before acceptance.

## IV. Decision
REVISE. This is a fail-closed stopgap, **not globally World-qualified lot identity**. A duplicate local lot remains unharvestable rather than being uniquely identified. It does not demonstrate ecological improvement. Existing 100 Founder identities, physical fuel/matter and CE remain unchanged.

## V. Reconciliation / queue
Core, Integration, Outer, main unchanged. Development is ahead of Core/Integration/Outer and diverged one behind main; PR #3 remains draft and must not be merged. Next: reconcile exact-source fingerprint, pass CI and the new regression, then implement true World-qualified lot IDs atomically across Tree production, Book holdings, harvest, exchange, ingestion/digestion, and checkpoint replay. Preserve G0/G1 historical-only acceptance, G2/G3 unpromoted, G4 ecological stability unverified, WB-PKG not live-approved. Queue remains P1-09 native identity read-only reconciliation, P1-10 independent two-World single-Book scheduling, P2-11 WB-PKG-gated gameplay, P2-12 CIV-OS research.

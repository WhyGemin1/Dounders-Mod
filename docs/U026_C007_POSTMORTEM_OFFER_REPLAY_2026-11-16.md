# U026 C007 — Five-phase engineering handoff (2026-11-16)

Decision: **REVISE**, no promotion or ecological claim.

## I — Source audit and causal hypothesis
Fresh Development vs Core comparison: Development 178 commits ahead before C007 and 180 after source/test commits, Core 0 ahead; no Core merge. The existing C020 resource agreement code correctly replayed accepted offers after separation or resource transfer, but decide_offer checked _active(recipient) before checking accepted/declined historical status. A Founder death after settlement therefore made an otherwise valid idempotent replay fail. The falsifier is a previously accepted/declined decision that becomes unreplayable after the recipient dies. Control: an open offer still cannot be newly accepted by a dead recipient.

## II — Actual source and test
- founders_civ/core/founder_exchange.py: move recipient activity guard below accepted/declined replay handling; keep original identity check, Book.move replay signature, and live-recipient check for new decisions.
- tests/test_c020_resource_agreements.py: test accepted replay after recipient death without another Book transaction or event, declined replay after death, conflicting replay rejection, and open-offer acceptance rejection after death.
- Source commit d5c8033af939e21acc82fa31fc2809ac6f22bc97.
- Test commit e34ed17b7baaaec261240c1a7f179fb68e457479.
- No changes to energy economics, WorldBox, native animals, Founder count or Book ledger.

## III — Test and run manifest
Source branch: Development. Current revision must be checked from live GitHub before test execution.
Local Python tests: **NOT RUN** (local container cannot resolve github.com; no checkout or source ZIP available here). CI for this exact revision: **NOT VERIFIED**. Historical run 43828001215: g1-matched SUCCESS; worldbox-source-offline SUCCESS; core151-python FAILURE; this is not evidence for C007.
Seeds/arms/horizons: **NOT RUN**. No ecological population or predator claims.
Book conservation: structural invariant retained by using existing replay Book.move, but new-revision conservation audit **NOT RUN**.
Source fingerprint: existing G2 candidate 515-file manifest is **STALE** for two edited Python files until a reviewed exact-source refresh. Promotion must fail closed.

Reproduction from checked-out exact Development source:
```sh
cd Founders_CIV_CoreCompletion151/source/world023024
PYTHONPATH=. python -m pytest -q tests/test_c020_resource_agreements.py
PYTHONPATH=. python -m pytest -q tests
```
Then run full provenance, G1 matched acceptance and checkpoint/replay jobs; capture exact commit, run ID, seed, arm, horizon, raw log and source SHA-256.

## IV — Decision
REVISE: a meaningful executable replay correction exists but is untested at this source SHA. No promotion to Core, no claim of improved ecological stability. Fail-closed fingerprint review is required.

## V — Branch and work queue
Development is implementation-only. Core, Integration, Outer and main unchanged by C007. Do not merge PR #3 until full exact-source regression and reviewer approval. Outer native WorldBox WB-PKG remains blocked without Windows assembly/version hook verification, signed/checksummed DLL, copied-save user logs, backup and rollback. G0/G1 historical Development acceptances remain historical, G2/G3 not promoted at current source, G4 unverified, G5+ blocked.

Next: refresh source manifest from exact Git bytes, execute focused/full CI, repair core151-python failure, then develop World-qualified physical lot identity across Tree production, Founder harvest, exchange, digestion and replay under one Book. Carry P1-09 native event identity, P1-10 two independently advancing virtual Worlds and P2-11 opt-in physical gameplay integration in the queue; never infer native WorldBox validation from offline tests.

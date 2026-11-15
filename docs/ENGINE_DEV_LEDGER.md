# Single-engine development ledger

## 2026-11-15 — unified engine cycle 1

- Main SHA at branch creation: `26a02ba50a53770b14eae0368315ea01036d0b3c`.
- Working branch: `feat/single-core151-authority`.
- Actual recovered source: local `Founders_CIV_Cycle152_SparseFounding_Experimental.zip` plus M01 runtime/gateway overlays from historical packages, including Cycle14 crash runtime. This engine retains the original Book and clock.
- Change: `src/founders_engine/authority.py`, `tests/test_authority.py`, `docs/SINGLE_ENGINE_AUTHORITY.md`, `engine/ACTIVE_ENGINE.json`. No alternate simulator implemented.
- Executed locally against recovered Core151 source: `PYTHONPATH=<patch>/src:<Core151>/source/world023024 python -m unittest discover -v -s <patch>/tests -p test_authority.py`: **6/6 passed**. One tick of actual `IntegratedWorld`, Book audit, 100 Founder check, invalid Founder claim rollback check, rejection of second Book and clock.
- Not run: GitHub CI, WorldBox in-game, complete Core151 regression suite, 30+ day ecological tests. No actual WorldBox mutation. Do not infer M05 live integration from its compiled source/repair instructions.
- Blocker: Core151 full Python source is available locally in the verified historical archive but is still not tracked as individual source files in GitHub. This PR is a tested integration boundary, not a complete executable engine checkout.
- Next: Git-track the original validated Core151 source files, reconcile M01 overlays, run full regression and Book checkpoint tests. Preserve all prior code history until verified migration.

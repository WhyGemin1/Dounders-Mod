# U026-C021 — World-qualified autonomous Tree production (2026-11-16)

Decision: REVISE. Development-only functional candidate; not promoted.

## I Baseline and falsifier
C020 GitHub Actions jobs passed (core151-python, g1-matched, worldbox-source-offline) at run 43969382708. Core, Integration, Outer remain c935c9a7066d6fe8d122a46edd2d8ce223343be2; main 26a02ba50a53770b14eae0368315ea01036d0b3c. Development was 208 commits ahead of Core before C021. Hypothesis: explicit World namespaces on Tree production eliminate identical local lot names across independent Worlds without changing existing single-World checkpoint identities. Falsifier: qualified lots collide, fail to propagate through Book accounts, or alter unqualified legacy IDs.

## II Executable implementation
- autonomous_provisioning.py: if a Tree has a validated world_id, prefix new physical lot identities with W-{world_id}-; legacy Trees retain original C003 identifiers. Invalid namespaces reject before production. Book, harvesting, trade, digestion and replay already carry lot strings as keys, but end-to-end two-World acceptance is NOT established.
- test_c020_resource_agreements.py: two tests for qualified production, checkpoint/Book preservation and invalid namespace rejection.
- exact-source fingerprint manifest refreshed.
Commits: source a44f7c4b59541f1d6555eb9b6a35ef1266e68b84; test 0c29ca6c749c75667baf54474bed24ded9107c3c; fingerprint 72543707872bebe4293a429f80a095b1f41712e7.
Source SHA256 52734ab944aeb06783d10d3b8a4d36e47e6958d29488bc51c1e465c690ec9c7d; test SHA256 0ff7682d36b4e6686142c9143ed92a41bd81b29326c12903d291cc1f2a61b4f4.

## III RUN_MANIFEST
Code ref 72543707872bebe4293a429f80a095b1f41712e7. Source: Development. Seeds: 829 and 830 as unit fixtures only. Arms: qualified production and invalid namespace. Horizons: 17 and 8 simulated steps inside new tests, NOT confirmed executed. Current-source CI, conservation, checkpoint and matched ecological trials: pending. No pass is claimed. Historical C020 CI passed on older source.

## IV Ecological analysis and decision
REVISE. This changes production identities, not food availability or ecological recruitment. No evidence of population or Tree stability improvement. Explicit world_id must be assigned uniquely by the authoritative scheduler; independent two-World scheduler and collision tests remain unfinished.

## V Reconciliation, rollback and next assignment
No Core, Integration, Outer or main changes. Draft Development-to-Core PR #3 remains unmerged. Rollback C021 by reverting fingerprint, test and source commits in reverse order after verifying ancestry. Do not delete historical artifacts or force push. Next: run current-source CI, fix failures, test two independently advancing Worlds sharing one Book with identical Tree/local lot identifiers, then validate harvest, barter, digestion, replay and source tamper controls. Outer retains WB-PKG Windows build, observer epochs, safe adapter, backup/rollback and copied-save gate; no live WorldBox test.

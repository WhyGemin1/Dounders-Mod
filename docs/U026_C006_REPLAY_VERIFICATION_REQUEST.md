# U026 C006/G1 replay and compatibility re-verification

**Verification-only draft PR — do not merge.**

This PR carries only this review request atop Development's current exact-source candidate. CI must execute G1 focused, G2 focused, full Core151, WorldBox offline, and exact 515-path source provenance.

Corrections under review:
- The existing Book ingestion receipt authorizes an exact replay even after portable food was consumed.
- Identical replay does not duplicate `founder_food_ingested` social events; forged ownership remains rejected.
- `test_integration_025.py` names all five SHA-256-confirmed tracked deviations from immutable WORLD-024 baseline.
- Test runner installation is not skipped on a provenance failure, preventing misleading `No module named pytest` cascades.

**Exit rule:** no promotion based on this PR alone; require passing full suite and independently reviewed gate.

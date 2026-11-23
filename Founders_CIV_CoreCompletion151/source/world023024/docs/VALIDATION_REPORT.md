# Founders-CIV v0.18 — Release Validation Report

**Date:** 2026-11-05  
**Scope:** pre-integration canonical documentation, preserved v0.17 mechanics, new v0.18 observability.  
**Executed:** yes, locally. **Empirical validation:** no.

## Test results

| Validation item | Observed result |
|---|---|
| Automated Python suite | **46/46 passed** (`python -m unittest discover -s tests -q`) |
| Node JS syntax check | Passed (`node --check web/app.js`) |
| 30-day sample | Seed 42, arm 1111, **286 initial actors**, 17,301 transactions, 2,812 exported significant events |
| 30-day mass residual | −1.82×10⁻¹¹ abstract mass units |
| 30-day energy residual | −8.94×10⁻⁸ experimental EU (vs ~312,696 EU tracked) |
| 120-day stress | Seed 1729, arm 1111, completed in ~4.8 seconds locally |
| 120-day mass residual | −7.91×10⁻¹¹ abstract mass units |
| 120-day energy residual | −2.34×10⁻⁷ experimental EU |
| Local API workflow | `/api/catalog` returns 25 systems; `/api/run` launches and saves; `/api/status` reports progress; `/api/result/<id>` loads; bad days are rejected (HTTP 400) |
| Browser UI smoke test | Canvas world and chart render, day changes, 25-system register populated; no JavaScript errors in tested offline injection flow |
| Version honesty | Operational 4 / Partial 17 / Specified 4; registered 480-run experiment explicitly not executed |

## Environmental findings—not success certificates

The 120-day stress run ended with 20 predators alive, 60 herbivores alive (initially 120), and 226 total living actors. Creation deaths were zero in this particular run. These results do **not** demonstrate an ecologically sustainable equilibrium or a functioning multi-generational society. The current engine does not implement reproduction and therefore cannot validate long-term population stability.

## Simulation versus 2D animation

Habitat membership, plant/soil/water/detritus/carcass material, actor health, skill records, social links, House reserve and institutional accounts are exported from the engine. **XY dot positions, movement sway, stylized vegetation shapes and light streaks are presentation only**. The dashboard intentionally does not claim that these shapes constitute engine-based pathfinding, climate dynamics, precise world geometry or physical light transport.

## Negative findings and engineering gaps

- Full biochemical mass/energy constraints are missing: abstract one-component material can pass conservation tests without chemical realism.
- The House and ten Underworld layers exist, but delayed energy flow, reserve-feedback control and Founder-driven sunlight policy are simplified.
- The core does not implement births, genetic inheritance, true multi-generational traditions or the full Soul Network hierarchy.
- Many institutional procedures remain small prototypes; independent political governance, capture, dissent and successor selection require further work.
- The register includes story-level canon that is not executable; this is intentional and labeled.
- The 480-run, 720-day factorial experiment remains only a registered research plan.

## Deployment checks

On Windows, extract ZIP; run `RUN_TESTS.bat`, then `START_DASHBOARD.bat`. In the browser run a 15-day scenario with factor arm 1111, drag the time slider, select an animal/habitat, inspect the energy and institution panels, then export JSON and cross-check `results/<job>/summary.json`. No outside network connection is required.

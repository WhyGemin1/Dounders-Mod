# v0.20 + Soul Network Animal Ecology — selective research pilot

This is a **self-contained continuation of v0.20**, not v0.21's finalized main engine. The v0.20 population/physical modules are present unchanged; the new adapter and experiment runner live at the package root.

## Windows instructions

Open Command Prompt inside the extracted folder. Run:

```cmd
py -m unittest -v test_soul_ecology test_continuity_loop
py run_soul_ecology.py --seeds 40 --steps 12 --out results/my_first_soul_trial
```

Or double-click `RUN_SOUL_ECOLOGY_TESTS.bat` / `RUN_SOUL_ECOLOGY_EXPERIMENT.bat`.

To run the 30-step demographic stress test:

```cmd
py run_soul_ecology.py --seeds 30 --steps 30 --out results/my_long_soul_trial
```

To rerun the no-hazard control:

```cmd
py run_soul_ecology.py --seeds 40 --steps 12 --no-hazard --out results/my_nohazard_control
```

No third-party Python modules are required. The original `run_continuity_loop.py` remains available and unchanged.

## Files

- `SOUL_NETWORK_ECOLOGY_SPEC.md` — proposed canon-aligned rule specification and research provenance.
- `soul_ecology_v021.py` — actor-level episodic/source memory, route confidence, skill practice, fear-guided migration and controlled seasonal hazard fixture.
- `run_soul_ecology.py` — deterministic A/B pilot, CSV/JSON time series.
- `test_soul_ecology.py` — 11 targeted learning and ledger tests.
- `analyze_soul_ecology.py` — paired 95% bootstrap confidence intervals and memory-decay sensitivity.
- `results/40_hazard`, `results/40_no_hazard`, `results/30_long`, `results/soul_ecology` — generated test evidence.
- `ECOLOGY_TEST_REPORT.md` — limitations and interpretations.

## Critical caution

The model uses an abstract iteration/generation step, not a biological day. The world hazard overlay was created to make route knowledge causally testable, with identical rules in all arms. Original v0.20 reproduction is **not fixed**: extinction at 30 steps persists in every arm. A passed ledger audit does not mean ecological sustainability.

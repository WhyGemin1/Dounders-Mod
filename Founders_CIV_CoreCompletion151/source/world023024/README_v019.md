# Founders-CIV v0.19 — Four Specified-System Prototypes

This **experimental extension** accompanies and preserves the tested v0.18 Observatory. It adds four independent executable modules: 100 Founder identity/checkpoint continuity, advanced Soul hierarchy gates, biological/cultural inheritance, and energy-maintained constructs/dimensions.

**These prototypes are NOT automatically enabled in the live dashboard or core simulations.** Existing v0.18 `START_DASHBOARD.bat` and `run_simulation.py` behave as before. The v0.18 canon register still describes what is live; the new design document describes tested extensions.

## Windows quick start

Extract the folder completely. Double-click `RUN_FOUR_PROTOTYPES.bat` or run from Command Prompt:

```powershell
py -m unittest discover -s tests -v
py run_four_prototypes.py
```

The first command runs original v0.18 regression tests alongside the v0.19 tests. The second runs reproducible isolated demonstrations and writes:

- `results/experimental/sample_results.json`
- `results/experimental/evolution_trials.csv`

For the existing interactive v0.18 Observatory, double-click `START_DASHBOARD.bat`. The new prototype data can be opened with Python, spreadsheets, or a text editor; a dedicated UI panel for the four experimental systems is **future work**.

Full rules and roadmap: [`docs/V019_FOUR_SYSTEMS_DEVELOPMENT.md`](docs/V019_FOUR_SYSTEMS_DEVELOPMENT.md).

## Module locations

- `founders_civ/experimental/founders.py`
- `founders_civ/experimental/soul.py`
- `founders_civ/experimental/evolution.py`
- `founders_civ/experimental/constructs.py`
- `tests/test_four_systems.py`
- `run_four_prototypes.py`

All share the **v0.18 authoritative Book** rather than implementing a competing material/energy ledger. The exceptions are explicitly acknowledged: immortal body mass and complete dimension geometry are outside the prototypes' modeled state.

No additional Python packages or cloud services required.

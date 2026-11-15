# SOCIAL-021 — Autonomous Founders Pilot

Adds an opt-in experimental social decision loop to the v0.20 compatibility candidate while preserving the existing physical engine unchanged.

- Start with `python -m unittest discover -s tests -q` (85 tests expected).
- Run `python -m unittest -q test_soul_ecology test_continuity_loop` (15 more independent tests).
- Run `python run_social_agents.py --seeds 25 --ticks 30 --workers 4 --out results/social_agents_25`.
- View the included offline `social_observatory.html` and/or generate a fresh `results/social_agents_25/social_observatory.html` with `build_social_dashboard.py`.
- On Windows you can double-click `RUN_SOCIAL_25.bat` with Python 3.10+ installed.

Read `docs/SOCIAL_AGENT_SPEC_v021.md` for source canon vs experimental distinctions and `docs/SOCIAL_25_SEED_REPORT.md` for findings and limitations.

**Warning:** This is a SOCIAL-021 *experimental branch*, not a fully merged Founders-CIV v0.21 master release. It has one authoritative Book *within the social pilot*, but it does not yet share a single actor registry and event clock with `founders_civ.core.engine.Simulation`. No claim of human psychological or consciousness validation.

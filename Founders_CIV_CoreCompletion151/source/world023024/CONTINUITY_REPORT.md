# Founders-CIV v0.20 experimental continuity loop

## Source and scope
Uses **unmodified** v0.19 Founder, Soul, Evolution, Construct and Book modules. `run_continuity_loop.py` is a new orchestration layer. It initializes one authoritative Book by copying the pre-freeze initial stocks from Population, adds dimension construction resources, then redirects Population to that same Book before running Founder and Construct operations. This is a first integration smoke test, not a full main-engine merge.

## Reproducible commands
```
python -m unittest discover -s tests -q
python run_continuity_loop.py --days 8 --seeds 6 --out results/continuity_8d
python run_continuity_loop.py --days 30 --seeds 6 --out results/continuity_30d
```

## Tasks in each iteration
1. Attempt social transmission of learned route (when teaching enabled; every third iteration).
2. Update individual animal metabolism, foraging, aging, selection, reproduction, migration and parent-to-child teaching.
3. Fund dimension maintenance (when enabled; every third iteration), then process its stability and possible collapse.
4. Trigger a Founder death and checkpoint restoration (when shock enabled); perform a later checkpoint.
5. Practice and attempt an existing Soul State activation only if the State survived checkpoint rollback.
6. Audit material and energy balances.

## Four matched conditions
- full: Founder death + teaching + refueling
- no_shock: no Founder death, teaching + refueling
- no_teaching: Founder death, no extra teaching, refueling (parental teaching within Evolution remains on)
- no_refuel: Founder death + teaching, no maintenance top-up

## Results (6 seeds, 24 runs per duration)
8 iterations: full population 53.33, route holders 11.0; no_shock 53.33/11.0; no_teaching 52.5/2.5; no_refuel 53.33/11.0. Dimension collapse in 6/6 no_refuel runs and 0/6 others. Founder rebirth in 6/6 shock arms.

30 iterations: animal extinction in all 24 runs. Dimension collapse in 6/6 no_refuel runs; none in other arms. Maximum absolute aggregate mass error 8.19e-12 and energy error 2.44e-10 synthetic units. All 66 pre-existing unit tests pass.

## Critical observations and limitations
- Initial orchestration failed because the post-checkpoint Soul State had been erased. Scheduler now checks State availability before attempting activation. This is a genuine cross-system continuity effect.
- The ecology lacks replenishment and therefore collapses in long runs. Physical conservation does not imply ecological sustainability.
- Founders and animals share one ledger, but the Founder's actions do **not** yet manage food stocks, teach animals, or maintain the dimension via an autonomous decision process. Refueling is a scripted treatment. This is **coupled bookkeeping and scheduling**, not yet emergent four-way causal integration.
- The four-system prototypes use synthetic parameter values; none of the survival, mutation, decay, teaching, or activation thresholds should be canonized.
- The loop does not integrate the full 100 Founders into autonomous tasks, all six Spirit types, institutions, advanced Soul State coordination, or complete habitat grids.
- The 8 and 30 steps of the Population engine represent abstract generations, not calendar days; avoid interpreting these as 8 or 30 real days.

## Next engineering gates
1. Add replenishment of nutrients, sunlight-driven biomass, carrying capacity, and seasonal migration; then run 100+ step population persistence checks.
2. Make Founder and animal tasks event-driven: Founder research -> teachable memory -> learner practice -> adaptive behavior -> measurable resource outcome.
3. Connect construct upkeep to actual actors' labor and institutions, with consequences for occupants and materials after collapse.
4. Ensure checkpoint rollback affects relationships and third-party memory independently.
5. Expand 6 to 30+ matched seeds, report trajectories and uncertainty, and only then attempt a full factorial study.

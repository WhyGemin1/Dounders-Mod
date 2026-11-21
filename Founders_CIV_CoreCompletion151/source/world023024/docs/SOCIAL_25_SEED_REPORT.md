# SOCIAL-021 · 25-seed social agency experiment report

**Executed:** 6 Nov 2026. **Status:** reproducible synthetic computer experiment; *not* empirical human social science.  
**Inputs:** 25 matched seeds 400–424, 100 Founders, 30 abstract decision cycles, 6 experimental policy conditions. Each Founder selects one action per cycle; 150 runs represent 450,000 decision opportunities. All runs passed material/energy balance checks. `Book` is conservation authority within the standalone social pilot.

## Interventions

- **full**: reciprocal pair contact priority; dynamic source trust, teaching, faction proposals and commitments.
- **no_partner**: same pairs exist historically, but their preference boost is removed from contact selection and choices.
- **no_teach**: no actor-to-actor teaching; local study still exists.
- **no_faction**: no faction proposals, endorsements, recruitment or formed coalitions.
- **neutral_trust**: trust used by decisions is fixed to 0.5, and feedback does not update trust.
- **isolated**: no social contact; individual study, practice and exploration remain possible.

## Observed per-run means

| Outcome | full | no_partner | no_teach | no_faction | neutral_trust | isolated |
|---|---:|---:|---:|---:|---:|---:|
| Formed factions | 8.12 | 9.00 | 7.80 | 0 | 8.44 | 0 |
| Faction members | 35.56 | 38.28 | 35.88 | 0 | 37.20 | 0 |
| Cross-squad factions | 7.96 | 8.88 | 7.68 | 0 | 8.04 | 0 |
| Founders with at least one information encounter | 99.72 | 99.72 | 92.68 | 99.84 | 99.56 | 99.88 |
| Information encounters | 753.36 | 771.72 | 595.92 | 800.12 | 757.88 | 1135.32 |
| Cross-squad teaching events | 162.48 | 156.36 | 0 | 186.20 | 167.28 | 0 |
| Mean Founder partner-benevolence expectation | .54655 | .50365 | .54949 | .54692 | .50000 | .50000 |
| Mean sum of six skill values | 1.14670 | 1.14938 | 1.15510 | 1.15208 | 1.14683 | 1.23541 |
| High-ambition-quartile skill gain | .13898 | .13935 | .14775 | .14474 | .13763 | .24170 |
| Low-ambition-quartile skill gain | .07869 | .08201 | .08575 | .08354 | .08053 | .14903 |

## Within-seed paired bootstrap comparisons, full minus alternative

- **Teaching:** full minus no_teach = **+7.04 informed Founders** (95% bootstrap interval **+5.76 to +8.56**) and **+157.44 information encounters** (+146.64 to +168.04). Teacher time partly displaces direct practice; full's aggregate skill is **−0.00840** lower than no_teach (−0.01023 to −0.00641).
- **Partner preference:** full minus no_partner = **+0.04290** in mean partner benevolence expectation (+0.04104 to +0.04461), **+6.12 cross-squad lessons** (+0.84 to +10.96), but **−2.72** faction members (−6.00 to +0.44). Extra pair contact may compete with wider coalition building.
- **Factions:** no_faction disables coalition formation, but full has **−46.76** fewer knowledge encounters compared with no_faction (−55.72 to −37.64): institution-building spends attention and energy that could otherwise go toward teaching or study. This does **not** show factions are socially bad; they have no collective benefits or resource projects yet, so the comparison is structurally incomplete.
- **Trust:** full minus neutral_trust = **+0.16 informed Founders** (−0.12 to +0.44) and **−0.00013** average aggregate skill (−0.00152 to +0.00120). Directional trust updates work, but the currently implemented choice policy gives trust too little consequential influence on aggregate results. Trust should be calibrated and tested in risks where reliance matters.
- **Isolation:** isolated agents achieve **+0.08871** mean total skill more than full agents because they are not spending actions on others. This is a programmed trade-off and a serious reminder to measure shared welfare, expertise diffusion, and institutional outcomes rather than optimize a single skill score.

## Scientific interpretation and failures

1. These trials show that the **specified decision policies execute** and produce different outcomes. They do not independently validate their psychological realism.
2. Founders start together at the House, so local information is frequently accessible. By cycle 30 nearly all know *something*, even in isolation. "Informed" is an overly weak endpoint; future tests must measure **accuracy, partial understanding, skill application, contradictory claims, source provenance, and differentiated knowledge domains**.
3. Historical partnerships were randomly assigned, and the squads/office ID assignment is a temporary test arrangement. The project source defines the squad structure and special partners, but not this numeric membership mapping.
4. Factions are interest coalitions requiring three supporters, not autonomous institutional projects. Their immediate action costs cannot be weighed against long-run social benefits until they control resources, coordinate labor and allocate production.
5. Ambition causes higher action priority and practice growth by **design**; high-ambition actors accrued approximately 0.139 mean skill gain versus 0.079 among low-ambition actors in the full condition. This is neither a calibrated effect size nor proof of a human psychological theory.
6. Integrity judgments based on unmet deadlines may be incorrect: a missed promise can be caused by insufficient energy or isolation. The simulation records unfulfilled promises without claiming to identify deceit.
7. All six conditions are separate policies that may alter **which actions get attempted**, not single-factor interventions with constant action exposure. Future studies should add fixed-time and fixed-opportunity controls, then test all mechanisms with ablations.
8. Neither consciousness nor actual Soul Network power development is established by these cognitive behavior experiments.

## Highest-priority engineering improvements

**Gate A — shared master loop.** Insert the social decision process as an opt-in replacement for core founder placeholders with one `Book`, one event log, one Founder population, and the existing daily clock. Compare 15-day results with canonical v0.18 controls.

**Gate B — physical collaboration.** Give factions resource accounts, explicit projects and governance. Make a collaborative action produce material results only through funded `Book` transactions and assign credit to participating Founders. Test that disabling their labor eliminates any output advantage.

**Gate C — credible trust.** Introduce task-specific reliability and material risks, distinguish lack of ability from unwillingness and external obstacle, test promises with independent evidence, and measure **trust calibration**, not only mean trust.

**Gate D — knowledge realism.** Replace additive saturation with delayed retrieval, spaced practice, partial understanding, knowledge prerequisites, and source quality. Preserve spatial and social information access constraints.

**Gate E — historical continuity and political competition.** Replace provisional SQ01–SQ08 membership and officers with the verified user-authored roster, then allow factions to negotiate, cooperate, fragment or contest authority as consequences of actions and perceived legitimacy.

## Files

- `results/social_agents_25/runs.csv`: all 150 individual arm/run metrics.
- `results/social_agents_25/summary.json`: arm means, standard deviations, and paired bootstrap intervals.
- `results/social_agents_25/sample_events.jsonl`: every traced decision/physical/social consequence in the representative 30-cycle run.
- `results/social_agents_25/demo_observatory.json`: replayable actor and faction snapshots for sample seed 400.
- `social_observatory.html`: offline viewer (no network requirements), clearly schematic rather than actual Sea geography.

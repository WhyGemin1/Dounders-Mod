# Founders-CIV v0.16 — Integration Architecture and Operational Research Protocol

**Status:** Proposed architecture and test specification. Existing user-established universe mechanics remain canonical; implementation details and numeric thresholds below are provisional.

## Core proposition
Every meaningful change in Founders-CIV is caused by one or more events. Each event updates a set of authoritative entities and produces observations that individual actors can perceive, remember, interpret, and act upon. Social norms and institutions emerge from repeated interactions and organized commitments, not from population-wide bonuses or thresholds alone.

## 1. Inherited canon
- The Wellspring supplies energy via rivers surrounding the House; the House possesses a vast stored reserve, emits a minimum sunlight output, and emits an additional proportion of incoming energy. Sunlight is allocated to worlds/dimensions, where actual exposure follows Founder-controlled daylight policies. Every energy debit has a corresponding credit.
- A universal toll applies when the internal material state changes. Movement and title/ownership transfers alone do not incur this transformation toll. House/world/Underworld split remains qualitative canon; sample percentages are test settings.
- Actors: 100 Founders in ultimate simulation; creations and six Spirit classes (Knights, Emperors, Assassins, Castors, Archers, Berserkers). All animals are actors, capable of Soul Network development, learning, and social transmission. Species define biological possibilities; training and experiences govern learned performance.
- Soul Networks: actions cause experience events, recorded in memory; relevant connected experiences and practice develop schemas, Nodes, States; higher organizations include Kingdoms (3+ coordinated States), Nations (4+ States, organizational), Realms (4+ Kingdoms and Emperor Node). Genuine overload is exceptional and requires excessive uncontrolled energy/force, not ordinary State use.
- Actor cognition includes physiological needs, safety, attachment/belonging, esteem/status, self-actualization; fear interpretation, spiritual convictions, willingness, capability, imperfect expectations, and self-directed goals.
- RSW is normative/meaning aspect; PSW instrumental/coordination aspect. Shared interpretations may produce durable beliefs and religion, with dissent, schism, coercion, institutional capture, and revision all possible.
- Nested spatial layers: world, region, habitat patch, space, material, element. The material state has one authoritative owner/account; other grids are views and indexes, not duplicate inventories.

## 2. Entity design

| Entity | Authoritative fields | Important relationships |
|---|---|---|
| Actor | ID, species, age, health, metabolism, reserves, carried inventory refs, current location, needs, skills, remembered events, schemas, Nodes, convictions, plans | kinship, social edges, group membership, Teacher/Student |
| MaterialBatch | ID, state_version, components/mass, embodied energy, accessible stored energy, purity, location, possession, owner | recipe, production events, habitat |
| EnergyAccount | account ID, balance, type, location, access constraints | source/target entries on ledger |
| Patch | ID, area, neighbors, soil/water/biomass references, exposure, seasonal conditions | region and world |
| Relationship | directed (source,target), type, trust, attachment, respect, dependence, frequency, history | actors; can be unequal in two directions |
| Group | membership, collective projects, claims, rules, obligations, pooled resources, governance | can nest and overlap |
| Institution | established practices, RSW meaning/limits, PSW work procedure, authority, budgets, succession, monitoring, sanctions and rights | actors/groups/resources |
| KnowledgeClaim | proposition, source, actor's confidence, supporting/counterevidence, source reliability, version | memory/events/teachers |
| Event | ID, step, actor, location, action, causal parent(s), inputs/outputs, actual result, observations, affected entities, evidence | cross-system journal |

**World truth and agent belief must be separate databases.** An actor receives only observations accessible by its perception, location, relationships, and means of communication. A myth or report can spread without changing the objective world state.

## 3. Atomic event/transaction contract

1. Read snapshot of world and actor-local observations.
2. Actor constructs feasible candidate plans; each plan references resources, relevant skills, and expected outcomes.
3. Scheduler resolves conflicts and atomically reserves resources so no material/energy can be spent twice.
4. Execution applies exact debits and credits; for state transformations, energy-work and toll are calculated and distributed.
5. Ledger validates conservation and nonnegative availability. An invalid transaction fails/rolls back and produces a failure event.
6. The event is appended to immutable history.
7. Other actors receive partial, possibly noisy observations; observers create source-tagged memories.
8. Skills/schemas/Nodes update only through qualifying remembered and practiced experience; relationship trust and belief confidence update based on observed outcomes.
9. Repeated cooperation may create group coordination; institutions arise only when obligations, rules, and ongoing collective operations can actually be identified.

**Accounting invariant:** For every energy transaction, total debits = total credits; separate explicit account for the Wellspring as externally specified inflow. For normal non-nuclear transformations, tracked matter components must balance. Nuclear mass-energy changes require the mass defect to be converted explicitly, not simultaneously counted as both matter and energy.

**Toll invariant:** Charged exactly once for each registered state-transition event, funded by energy involved in that process. A mere change of location, ownership, or description is not a material-state transition. Fine molecular transitions may be coarse-grained into an audited metabolic or processing event, but cannot be both charged microscopically and again as a whole.

**Energy-accessibility invariant:** usable energy reserve, embodied/rest energy, latent chemical energy, waste heat, and work-in-progress cannot be treated as fungible without an explicit transformation and efficiency bound. Lack of accessible energy can coexist with high total energy.

## 4. Cognitive, social and RSW causal pipeline

Perceived needs and fears → interpreted meaning and expectations → available goals and obligations → candidate actions/plans → willingness and feasibility → action → outcome event → memory → revised expectations, skills, values, social links → future decisions.

A plan contains: goal, motivating needs, predicted benefit, expected risk, resource requirements, collaborators, checkpoints, abandonment conditions, and alternative strategies. An actor can persist for multiple steps, switch goals, make errors, or decline collective action.

Social learning must distinguish: (a) exposure to information, (b) belief acceptance, (c) practical training, (d) competence, (e) social conformity, and (f) spiritual commitment. None implies all others. Teacher knowledge may be correct or wrong; coercive conformity can mimic public agreement while private confidence differs.

RSW and PSW are both recorded for **every** organized activity, including irrigation, guilds, families, ritual, courts and schools. Example: a food-sharing group may have a moral obligation to avoid abandonment (RSW), distribution rules/stockpile managers (PSW), and a leadership/appeal process (governance).

## 5. Spatial/time integration

| Update scale | Examples |
|---|---|
| Event/substep | Harvest, hunt, consume, transfer, communicate, transform, teach |
| Hour/day | House sunlight delivery, actor homeostasis, movement, routine work |
| Week | Relationship change, project progress, stockpile replenishment, learning review |
| Season | Migration and breeding, harvest, climate, daylight decisions |
| Year/generation | Biological aging, inherited traits, cultural succession, institutional change |

One physical stock register; multiple spatial indexes. Update fine-grained particles/material organization only for actual transformations or specialized Soul Network activity. Most habitats run at aggregate material-compartment resolution while individuals move as actors.

## 6. Operational test protocol

For every experiment provide:
- Research question, causal mechanism, competing explanation, outcome variable(s), qualitative prediction.
- Canon/version hash, all provisional parameter values, world seed, agent seed, environmental shock schedule, scenario ID.
- Baseline, ablation(s), negative control, adversarial stressor; matched initial conditions and random-number streams where feasible.
- Every-step material and energy audit, consistency assertions, invalid-operation counts.
- Agent-level event traces and aggregate outcomes with confidence intervals, failure rates, and cross-seed variability.
- Cost incidence: which actors/groups gain, who loses; no unsupported claim that increased average welfare means improved welfare for all.
- Predetermined falsification criteria; revise model only after evaluating independent hold-out scenarios.

### Recommended integrated pilot: Two Worlds / Shared House / Four Settlements
- One Wellspring and House; two Founder-controlled daylight policies; ten Underworld layers; four habitats per world, with weather and connected migration routes.
- Each world contains 2 settlements of 24 creations, 2 Castors, herbivores, pack hunters, ambush hunters, scavengers, decomposers, and ecological materials.
- Each creation begins with a network of caregivers/relatives/friends/neighbors/mentor links and one private long-term goal; actor beliefs and knowledge vary despite matching aggregate statistics.
- Run 720 days with a food drought and misinformation shock that are identical across matched seeds. Founder policies may adapt, but policies and objective functions are specified before running.
- Primary experimental factors: (1) social network diversity on/off, (2) private Fear Logic/commitments on/off, (3) shared collective commitment process on/off, (4) institutional enforcement/feedback on/off. 16 factorial arms × 30 seeds = 480 runs for an initial statistical study.
- Daylight, species physiology, and initial resource stocks stay constant across arms; follow-up cross-world experiment changes daylight orthogonally.

## 7. Priority operational tests
1. Resource audit: tree felled → lumber → shelter → decomposition; assert identical matter/energy accounting and toll charged for actual states only.
2. House cycle: low Wellspring inflow / high sunlight / delayed Underworld return; verify reserve depletion, no sunlight without fuel, and no simultaneous double-counting of House return.
3. Species learning: pack versus ambush hunts, animal social teaching and migratory routes; evaluate prey/predator persistence and hunting costs without a forced success rate.
4. Intergenerational teaching: compare no social ties, kin only, kin + mentors, full heterogeneous networks; evaluate skill retention, knowledge errors, and social mobility.
5. RSW × PSW: cross spiritual conviction strength and instrumental capability; test whether belief without ability fails, capability without agreement fragments, both help under certain conditions, and both can create capture/rigidity.
6. Information shock: false water-scarcity doctrine propagates via trusted relatives and a teacher; log private/public belief differences, belief correction, and incidence of shortages.
7. Long-term goal test: compare one-step utility, memory without planning, full planning; measure completed projects, exhaustion, long-term skill, opportunity costs.
8. Institution formation: form and dissolve a food-sharing organization only through repeated coordinated transactions, claims, legitimacy and governance; no named automatic group thresholds.
9. Daylight and migration: allow Founder decisions to change absorbed sunlight while respecting House distribution and local habitat constraints.
10. Adversarial capture: one family controls granary and teacher access; record output, inequality, dissent, compliance, and succession breakdown.

## 8. Mandatory rejection rules (precommitted)
- Reject any run that fails energy or material conservation (except explicitly defined external boundary flow).
- Reject 'social learning' claims if training advances without exposure, remembered events, practice, or knowledge source.
- Reject institutional emergence claims if a named institution appears from a fixed score without observable members, rules, pooled resources, or continuing practices.
- Reject RSW performance claims if shared belief directly boosts yields without an identifiable resource, labor, attention, coordination, or behavioral mechanism.
- Reject overfitted model conclusions if the direction of effects reverses in held-out seeds/scenarios or depends on arbitrary threshold tuning.
- Do not equate stable populations with stable ecological food webs, or survival of a norm with legitimacy.
- Do not interpret fictional model experiments as empirical confirmation of real-world social theory.

## 9. CIV-OS diagnostics for every society
For each institution record: sacred object/value, publicly declared model, implemented operational rules, public/private support, resource/control concentration, who bears cost, mechanism/latency of feedback, and counterevidence. Diagnose possible hollowing, rigidity, drift, calibration, capture, and brittleness as descriptive hypotheses, **not** automatic scored outcomes.

## 10. Methodological references
- Grimm et al. (2020), ODD protocol update (Overview, Design concepts, Details): https://doi.org/10.18564/jasss.4259
- Epstein & Axtell, *Growing Artificial Societies* (Sugarscape): https://mitpress.mit.edu/9780262550253/growing-artificial-societies/
- NetLogo BehaviorSpace: https://docs.netlogo.org/7.0.0/behaviorspace
- Mesa: https://mesa.readthedocs.io/stable/
- GAMA: https://gama-platform.org/wiki/Overview
- Ecopath with Ecosim: https://ecopath.org/about/
- Park et al. (2023), Generative Agents: https://doi.org/10.1145/3586183.3606763
- Centola & Macy (2007), Complex Contagions: https://doi.org/10.1086/521848
- Ostrom institutional design principles summary: https://www.ecologyandsociety.org/vol9/iss1/art18/table3.html
- Existing project sources: *CIV-OS-v1.1-system-patch*, *The-Dual-Core-Model-Tested*, *RSW V 1.2*.
